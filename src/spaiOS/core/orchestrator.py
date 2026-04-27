import base64

import ollama
from PyQt6.QtCore import QThread, pyqtSignal

from spaiOS.core import context as ctx
from spaiOS.agents.file_agent import DeleteConfirmationRequired, FileAgent, FileEntry

_MODEL = "llama3.2:3b"
_VISION_MODEL = "moondream:latest"


_CLARIFYING_PREFIXES = (
    "could you clarify",
    "can you clarify",
    "could you tell me",
    "can you tell me",
    "what do you mean",
    "which one",
    "could you specify",
    "could you provide more",
)


def is_clarifying_question(text: str) -> bool:
    stripped = text.strip()
    if stripped.endswith("?"):
        return True
    lower = stripped.lower()
    return any(lower.startswith(p) for p in _CLARIFYING_PREFIXES)


_BASE_SYSTEM_PROMPT = (
    "You are spaiOS, a helpful AI assistant running as a desktop overlay. "
    "The user has a personal file sandbox at ~/spaiOS-sandbox/ on their Linux machine. "
    "You have tools to manage that directory: list_directory, read_file_summary, "
    "create_folder, move_file, rename_file, delete_file. "
    "IMPORTANT: For any request involving files, folders, listing, organizing, moving, "
    "renaming, deleting, or reading — you MUST call the appropriate tool immediately. "
    "Do not ask for clarification about what 'sandbox' means. "
    "Do not describe what you would do. Just call the tool."
)


def _build_system_prompt(ctx_data: dict) -> str:
    parts = []
    if ctx_data.get("app_name"):
        parts.append(f"Active app: {ctx_data['app_name']}")
    if ctx_data.get("window_title"):
        parts.append(f"Window title: {ctx_data['window_title']}")
    if not parts:
        return _BASE_SYSTEM_PROMPT
    screen_section = (
        "\n\nAdditional screen context (for general questions only — "
        "do NOT use this to answer file management requests):\n" + "\n".join(parts)
    )
    return _BASE_SYSTEM_PROMPT + screen_section


def _format_entries(entries: list[FileEntry]) -> str:
    if not entries:
        return "(empty directory)"
    lines = []
    for e in entries:
        kind = "DIR " if e.is_dir else "FILE"
        size = f" ({e.size_bytes}B)" if not e.is_dir else ""
        lines.append(f"  {kind}  {e.path}{size}")
    return "\n".join(lines)


_FILE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in the user's sandbox directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Sandbox-relative path to list. Empty string for root.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new folder inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Sandbox-relative path for the new folder.",
                    }
                },
                "required": ["subpath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file or folder to a new location inside the sandbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Source path (sandbox-relative).",
                    },
                    "dst": {
                        "type": "string",
                        "description": "Destination path (sandbox-relative). "
                        "If this is an existing directory the file is placed inside it.",
                    },
                },
                "required": ["src", "dst"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file within its current directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "src": {
                        "type": "string",
                        "description": "Current file path (sandbox-relative).",
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New filename — bare name only, no path separators.",
                    },
                },
                "required": ["src", "new_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or empty folder. User confirmation required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Sandbox-relative path to delete.",
                    }
                },
                "required": ["subpath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_summary",
            "description": "Return a short preview of a file's content (first 500 characters).",
            "parameters": {
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Sandbox-relative path to the file.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 500).",
                    },
                },
                "required": ["subpath"],
            },
        },
    },
]

_CONFIRM_WORDS = {"yes", "y", "confirm", "ok", "sure", "proceed", "yep", "yup"}
_DENY_WORDS = {"no", "n", "cancel", "nope", "nah", "stop"}
_TOOL_LOOP_LIMIT = 10


class Orchestrator:
    _MAX_HISTORY_PAIRS = 10

    def __init__(self) -> None:
        self._history: list[dict] = []
        self._file_agent = FileAgent()
        self._pending_delete: str | None = None

    def ask(self, prompt: str) -> str:
        if self._pending_delete is not None:
            return self._handle_delete_response(prompt)

        ctx_data = ctx.capture()
        system_prompt = _build_system_prompt(ctx_data)
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(self._history)
        messages.append({"role": "user", "content": prompt})

        reply = self._run_with_tools(messages)

        self._history.append({"role": "user", "content": prompt})
        self._history.append({"role": "assistant", "content": reply})
        max_msgs = self._MAX_HISTORY_PAIRS * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]
        return reply

    def _run_with_tools(self, messages: list[dict]) -> str:
        loop_messages = list(messages)

        for _ in range(_TOOL_LOOP_LIMIT):
            response = ollama.chat(
                model=_MODEL, messages=loop_messages, tools=_FILE_TOOLS
            )
            msg = response.message

            if not msg.tool_calls:
                return msg.content or ""

            # Append the assistant turn (may include tool_calls)
            loop_messages.append(msg)

            for tc in msg.tool_calls:
                result = self._dispatch_tool(
                    tc.function.name, tc.function.arguments or {}
                )
                loop_messages.append({"role": "tool", "content": result})

                if self._pending_delete is not None:
                    return (
                        f"I need your confirmation to delete '{self._pending_delete}'. "
                        f"Should I go ahead? (yes/no)"
                    )

        return "I reached the tool call limit — please try a simpler request."

    def _dispatch_tool(self, name: str, args: dict) -> str:
        try:
            if name == "list_directory":
                entries = self._file_agent.list_directory(args.get("subpath", ""))
                return _format_entries(entries)
            if name == "create_folder":
                path = self._file_agent.create_folder(args["subpath"])
                return f"Created folder: {path}"
            if name == "move_file":
                new_path = self._file_agent.move_file(args["src"], args["dst"])
                return f"Moved to: {new_path}"
            if name == "rename_file":
                new_path = self._file_agent.rename_file(args["src"], args["new_name"])
                return f"Renamed to: {new_path}"
            if name == "delete_file":
                deleted = self._file_agent.delete_file(args["subpath"])
                return f"Deleted: {deleted}"
            if name == "read_file_summary":
                summary = self._file_agent.read_file_summary(
                    args["subpath"], args.get("max_chars", 500)
                )
                return summary
            return f"Unknown tool: {name}"
        except DeleteConfirmationRequired as exc:
            self._pending_delete = exc.path
            return "confirmation_required"
        except Exception as exc:
            return f"Error: {exc}"

    def _handle_delete_response(self, prompt: str) -> str:
        lower = prompt.strip().lower()
        path = self._pending_delete
        self._pending_delete = None

        if lower in _CONFIRM_WORDS:
            try:
                deleted = self._file_agent.delete_file(path, confirmed=True)
                reply = f"Done — deleted '{deleted}'."
            except Exception as exc:
                reply = f"Deletion failed: {exc}"
        else:
            reply = f"OK, I won't delete '{path}'."

        self._history.append({"role": "user", "content": prompt})
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def clear_history(self) -> None:
        self._history = []
        self._pending_delete = None

    def ask_with_vision(self, prompt: str, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        response = ollama.chat(
            model=_VISION_MODEL,
            messages=[{"role": "user", "content": prompt, "images": [b64]}],
        )
        return response.message.content


def _emit_ollama_error(exc: Exception, signal: pyqtSignal) -> None:  # type: ignore[type-arg]
    msg = str(exc).lower()
    if "connection" in msg or "refused" in msg or "connrefused" in msg:
        signal.emit("Ollama is not running. Start it with: ollama serve")
    elif ("model" in msg and ("not found" in msg or "404" in msg)) or "pull" in msg:
        signal.emit(f"Model not found. Run: ollama pull {_MODEL}")
    elif "timeout" in msg or "timed out" in msg:
        signal.emit("Request timed out — Ollama may be busy. Try again.")
    else:
        signal.emit(f"Error: {str(exc)}")


class AskThread(QThread):
    result = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt: str, orchestrator: Orchestrator) -> None:
        super().__init__()
        self._prompt = prompt
        self._orchestrator = orchestrator

    def run(self) -> None:
        try:
            text = self._orchestrator.ask(self._prompt)
            self.result.emit(text)
        except Exception as exc:
            _emit_ollama_error(exc, self.error)


class AskWithVisionThread(QThread):
    result = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt: str, image_bytes: bytes) -> None:
        super().__init__()
        self._prompt = prompt
        self._image_bytes = image_bytes
        self._orchestrator = Orchestrator()

    def run(self) -> None:
        try:
            text = self._orchestrator.ask_with_vision(self._prompt, self._image_bytes)
            self.result.emit(text)
        except Exception as exc:
            _emit_ollama_error(exc, self.error)
