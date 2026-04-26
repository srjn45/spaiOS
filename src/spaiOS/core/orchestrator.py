import base64

import ollama
from PyQt6.QtCore import QThread, pyqtSignal

from spaiOS.core import context as ctx

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


def _build_system_prompt(ctx_data: dict) -> str:
    parts = []
    if ctx_data.get("app_name"):
        parts.append(f"Active app: {ctx_data['app_name']}")
    if ctx_data.get("window_title"):
        parts.append(f"Window title: {ctx_data['window_title']}")
    if ctx_data.get("visible_text"):
        parts.append(f"Visible text:\n{ctx_data['visible_text']}")
    if not parts:
        return ""
    return "Context from the user's screen:\n" + "\n".join(parts)


class Orchestrator:
    _MAX_HISTORY_PAIRS = 10

    def __init__(self) -> None:
        self._history: list[dict] = []

    def ask(self, prompt: str) -> str:
        ctx_data = ctx.capture()
        system_prompt = _build_system_prompt(ctx_data)
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(self._history)
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=_MODEL, messages=messages)
        reply = response.message.content
        self._history.append({"role": "user", "content": prompt})
        self._history.append({"role": "assistant", "content": reply})
        max_msgs = self._MAX_HISTORY_PAIRS * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]
        return reply

    def clear_history(self) -> None:
        self._history = []

    def ask_with_vision(self, prompt: str, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        response = ollama.chat(
            model=_VISION_MODEL,
            messages=[{"role": "user", "content": prompt, "images": [b64]}],
        )
        return response.message.content


def _emit_ollama_error(exc: Exception, signal: pyqtSignal) -> None:  # type: ignore[type-arg]
    msg = str(exc)
    if "connection" in msg.lower() or "refused" in msg.lower():
        signal.emit("Ollama is not running. Start it with: ollama serve")
    else:
        signal.emit(f"Error: {msg}")


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
