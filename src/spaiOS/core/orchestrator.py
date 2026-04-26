import ollama
from PyQt6.QtCore import QThread, pyqtSignal

_MODEL = "llama3.2:3b"


class Orchestrator:
    def ask(self, prompt: str) -> str:
        response = ollama.chat(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.message.content


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
            msg = str(exc)
            if "connection" in msg.lower() or "refused" in msg.lower():
                self.error.emit("Ollama is not running. Start it with: ollama serve")
            else:
                self.error.emit(f"Error: {msg}")
