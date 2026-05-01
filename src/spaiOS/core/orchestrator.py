import base64

import ollama
from PyQt6.QtCore import QThread, pyqtSignal

from spaiOS.core import context as ctx
from spaiOS.agents.chrome_agent import ChromeAgent, ChromeNotAvailable
from spaiOS.agents.code_agent import (
    CodeAgent,
    CommandBlocked,
    WriteConfirmationRequired,
)
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
    "You also have Chrome browser tools: open_url, search_web, get_current_url, get_page_content, "
    "click_element, fill_input, fill_form, click_link_by_text, get_tabs, clear_history. "
    "You also have code tools: read_file (read any file), "
    "write_file (shows diff + asks confirmation), "
    "run_terminal_command (run a shell command), open_in_editor (open file in $EDITOR). "
    "IMPORTANT: For any request involving files, folders, listing, organizing, moving, "
    "renaming, deleting, or reading — you MUST call the appropriate tool immediately. "
    "For any request to open a website, navigate to a URL, or go to a page — "
    "call open_url immediately. "
    "For any request to search for something on the web — call search_web immediately. "
    "For any request to read or summarize what's on the current page — call get_page_content. "
    "For any request to click a button or link on a page by its text — call click_link_by_text. "
    "For any request to click an element by CSS selector — call click_element. "
    "For any request to fill multiple form fields at once — call fill_form with a dict. "
    "For any request to fill a single form field — call fill_input with a CSS selector and value. "
    "For any request to list open tabs — call get_tabs. "
    "For any request to clear browsing history — call clear_history. "
    "For any request to read or view a file's content — call read_file. "
    "For any request to write, save, or modify a file — "
    "call write_file (a diff will be shown for confirmation). "
    "For any request to run a shell command or terminal command — call run_terminal_command. "
    "For any request to open a file in an editor — call open_in_editor. "
    "Do not describe what you would do. Just call the tool."
)


def _build_system_prompt(ctx_data: dict, memory_context: str = "") -> str:
    parts = []
    if ctx_data.get("app_name"):
        parts.append(f"Active app: {ctx_data['app_name']}")
    if ctx_data.get("window_title"):
        parts.append(f"Window title: {ctx_data['window_title']}")
    prompt = _BASE_SYSTEM_PROMPT
    if memory_context:
        prompt += (
            "\n\nRecent session history (use this to answer questions about "
            "what the user has been working on):\n" + memory_context
        )
    if parts:
        prompt += (
            "\n\nCurrent screen context (for general questions only — "
            "do NOT use this to answer file management requests):\n" + "\n".join(parts)
        )
    return prompt


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

_CHROME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": (
                "Navigate Chrome to a URL. Use when the user asks to open a website, "
                "go to a page, or visit a URL. Prepends https:// if no scheme given."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open, e.g. 'https://youtube.com'.",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search Google for a query and navigate Chrome to the results. "
                "Use when the user says 'search for', 'look up', 'find', or 'google X'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'lo-fi beats'.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_url",
            "description": "Return the URL currently loaded in the active Chrome tab.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": (
                "Return the visible text of the current Chrome page. "
                "Use to read, summarize, or answer questions about page content."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Click the first element matching a CSS selector in the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to click, e.g. '#submit-btn'.",
                    }
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_input",
            "description": (
                "Set the value of a form input element matched by CSS selector, "
                "then fire input and change events. Use for filling text fields, "
                "search boxes, or any form input."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the input, e.g. 'input[name=\"q\"]'.",
                    },
                    "value": {
                        "type": "string",
                        "description": "The text value to set.",
                    },
                },
                "required": ["selector", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_form",
            "description": (
                "Fill multiple form fields at once. Pass a dict mapping CSS selectors "
                "to values. Use when the user asks to fill in a form or enter multiple fields."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "object",
                        "description": "CSS selector to value mapping, e.g. {'#q': 'lo-fi'}.",
                        "additionalProperties": {"type": "string"},
                    }
                },
                "required": ["fields"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_link_by_text",
            "description": (
                "Click the first link on the page whose visible text matches link_text "
                "(case-insensitive). Use when the user says 'click the X link' or 'click on X'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "link_text": {
                        "type": "string",
                        "description": "The visible text of the link to click, e.g. 'Wikipedia'.",
                    }
                },
                "required": ["link_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tabs",
            "description": "Return a list of URLs for all currently open Chrome tabs.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_history",
            "description": "Clear Chrome browsing history.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_CODE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file at the given absolute path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file. Always shows a unified diff first and asks "
                "the user for confirmation before saving."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to write.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full new content of the file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Run a shell command and return its stdout+stderr output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "The shell command to run.",
                    }
                },
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_in_editor",
            "description": "Open a file in the user's $EDITOR (defaults to nano).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to open."}
                },
                "required": ["path"],
            },
        },
    },
]

_CONFIRM_WORDS = {"yes", "y", "confirm", "ok", "sure", "proceed", "yep", "yup"}
_DENY_WORDS = {"no", "n", "cancel", "nope", "nah", "stop"}
_TOOL_LOOP_LIMIT = 10


class Orchestrator:
    _MAX_HISTORY_PAIRS = 10

    def __init__(self, memory=None) -> None:
        self._history: list[dict] = []
        self._file_agent = FileAgent()
        self._chrome_agent = ChromeAgent()
        self._code_agent = CodeAgent()
        self._pending_delete: str | None = None
        self._pending_write: tuple[str, str, str] | None = (
            None  # (path, new_content, diff)
        )
        self._memory = memory
        self._memory_context: str = self._load_memory_context()

    def _load_memory_context(self) -> str:
        if self._memory is None:
            return ""
        sessions = self._memory.get_recent_sessions(5)
        if not sessions:
            return ""
        return "\n---\n".join(sessions)

    def remember_snippet(self, text: str) -> str:
        if self._memory is None:
            return "Memory is not available."
        self._memory.store_snippet(text)
        return f"Remembered: {text}"

    def end_session(self) -> None:
        if self._memory is not None and self._history:
            import datetime
            from spaiOS.core.summarizer import summarize_session

            summary = summarize_session(self._history)
            if summary:
                self._memory.store_session(
                    datetime.date.today().isoformat(), summary, [], []
                )
                self._memory_context = self._load_memory_context()
        self.clear_history()

    def ask(self, prompt: str) -> str:
        if self._pending_write is not None:
            return self._handle_write_response(prompt)
        if self._pending_delete is not None:
            return self._handle_delete_response(prompt)

        ctx_data = ctx.capture()
        system_prompt = _build_system_prompt(ctx_data, self._memory_context)
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
                model=_MODEL,
                messages=loop_messages,
                tools=_FILE_TOOLS + _CHROME_TOOLS + _CODE_TOOLS,
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

                if self._pending_write is not None:
                    path, _, diff = self._pending_write
                    return (
                        f"Here's the diff for '{path}':\n\n"
                        f"```diff\n{diff}\n```\n\n"
                        f"Apply this change? (yes/no)"
                    )
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
            if name == "open_url":
                return self._chrome_agent.open_url(args["url"])
            if name == "search_web":
                return self._chrome_agent.search_web(args["query"])
            if name == "get_current_url":
                return self._chrome_agent.get_current_url()
            if name == "get_page_content":
                return self._chrome_agent.get_page_content()
            if name == "click_element":
                return self._chrome_agent.click_element(args["selector"])
            if name == "fill_input":
                return self._chrome_agent.fill_input(args["selector"], args["value"])
            if name == "fill_form":
                return self._chrome_agent.fill_form(args["fields"])
            if name == "click_link_by_text":
                return self._chrome_agent.click_link_by_text(args["link_text"])
            if name == "get_tabs":
                tabs = self._chrome_agent.get_tabs()
                return "\n".join(tabs) if tabs else "No open tabs"
            if name == "clear_history":
                return self._chrome_agent.clear_history()
            if name == "read_file":
                return self._code_agent.read_file(args["path"])
            if name == "write_file":
                self._code_agent.write_file(args["path"], args["content"])
            if name == "run_terminal_command":
                return self._code_agent.run_terminal_command(args["cmd"])
            if name == "open_in_editor":
                return self._code_agent.open_in_editor(args["path"])
            return f"Unknown tool: {name}"
        except WriteConfirmationRequired as exc:
            self._pending_write = (exc.path, exc.new_content, exc.diff)
            return "write_confirmation_required"
        except CommandBlocked as exc:
            return f"Command blocked for safety: {exc}"
        except DeleteConfirmationRequired as exc:
            self._pending_delete = exc.path
            return "confirmation_required"
        except ChromeNotAvailable as exc:
            return f"Chrome not available: {exc}"
        except Exception as exc:
            return f"Error: {exc}"

    def _handle_write_response(self, prompt: str) -> str:
        lower = prompt.strip().lower()
        path, content, diff = self._pending_write
        self._pending_write = None

        if lower in _CONFIRM_WORDS:
            try:
                result = self._code_agent.confirm_write(path, content)
                reply = f"Done — {result}"
            except Exception as exc:
                reply = f"Write failed: {exc}"
        else:
            reply = f"OK, I won't write to '{path}'."

        self._history.append({"role": "user", "content": prompt})
        self._history.append({"role": "assistant", "content": reply})
        return reply

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
        self._pending_write = None

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
