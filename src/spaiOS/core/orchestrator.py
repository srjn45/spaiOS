import base64

import ollama
from PyQt6.QtCore import QThread, pyqtSignal

_MODEL = "llama3.2:3b"
_VISION_MODEL = "moondream:latest"


class Orchestrator:
    def ask(self, prompt: str) -> str:
        response = ollama.chat(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.message.content

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

    def __init__(self, prompt: str) -> None:
        super().__init__()
        self._prompt = prompt
        self._orchestrator = Orchestrator()

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
