from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QWidget

_INPUT_STYLE = (
    "QLineEdit { background: rgba(255,255,255,20); border: 1px solid rgba(255,255,255,40);"
    " border-radius: 8px; color: white; padding: 6px 10px; font-size: 14px; }"
    "QLineEdit:focus { border-color: rgba(140,120,255,180); }"
    "QLineEdit:disabled { color: rgba(255,255,255,60); }"
)

_RESPONSE_STYLE = (
    "QTextEdit { background: rgba(255,255,255,10); border: 1px solid rgba(255,255,255,20);"
    " border-radius: 8px; color: rgba(220,215,255,220); padding: 8px 10px; font-size: 13px; }"
)

_RESPONSE_ERROR_STYLE = (
    "QTextEdit { background: rgba(255,60,60,15); border: 1px solid rgba(255,80,80,40);"
    " border-radius: 8px; color: rgba(255,160,160,220); padding: 8px 10px; font-size: 13px; }"
)


class InputRow(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask anything…")
        self._input.setStyleSheet(_INPUT_STYLE)
        self._input.returnPressed.connect(self._on_submit)

        self._button = QPushButton("↵")
        self._button.setFixedSize(36, 36)
        self._button.setStyleSheet(
            "QPushButton { background: rgba(140,120,255,120); border: none; border-radius: 8px;"
            " color: white; font-size: 16px; }"
            "QPushButton:hover { background: rgba(140,120,255,180); }"
            "QPushButton:disabled { background: rgba(60,60,80,80); color: rgba(255,255,255,60); }"
        )
        self._button.clicked.connect(self._on_submit)

        layout.addWidget(self._input)
        layout.addWidget(self._button)

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self.submitted.emit(text)

    def set_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._button.setEnabled(enabled)

    def clear(self) -> None:
        self._input.clear()

    def focus(self) -> None:
        self._input.setFocus()


class ResponseView(QTextEdit):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(80)
        self.setStyleSheet(_RESPONSE_STYLE)

    def show_response(self, text: str) -> None:
        self.setStyleSheet(_RESPONSE_STYLE)
        self.setPlainText(text)

    def show_error(self, text: str) -> None:
        self.setStyleSheet(_RESPONSE_ERROR_STYLE)
        self.setPlainText(text)
