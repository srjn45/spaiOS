from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QWidget

from spaiOS.ui import tokens

_INPUT_STYLE = (
    f"QLineEdit {{ background: {tokens.BG_SURFACE}; border: 1px solid {tokens.BORDER_SUBTLE};"
    f" border-radius: 8px; color: {tokens.TEXT_PRIMARY};"
    f" padding: 7px 12px; font-size: {tokens.FONT_SIZE_MD}px; }}"
    f"QLineEdit:focus {{ border-color: {tokens.BORDER_FOCUS}; }}"
    f"QLineEdit:disabled {{ color: {tokens.TEXT_MUTED}; }}"
)

_RESPONSE_STYLE = (
    f"QTextEdit {{ background: {tokens.BG_SURFACE}; border: 1px solid {tokens.BORDER_SUBTLE};"
    f" border-radius: 8px; color: {tokens.TEXT_SECONDARY};"
    f" padding: 10px 12px; font-size: {tokens.FONT_SIZE_MD}px; }}"
)

_RESPONSE_ERROR_STYLE = (
    f"QTextEdit {{ background: {tokens.BG_ERROR}; border: 1px solid {tokens.BORDER_ERROR};"
    f" border-radius: 8px; color: {tokens.TEXT_ERROR};"
    f" padding: 10px 12px; font-size: {tokens.FONT_SIZE_MD}px; }}"
)

_BUTTON_STYLE = (
    f"QPushButton {{ background: {tokens.BG_ACCENT}; border: none; border-radius: 8px;"
    f" color: white; font-size: {tokens.FONT_SIZE_LG}px; }}"
    f"QPushButton:hover {{ background: {tokens.BG_ACCENT_HOVER}; }}"
    f"QPushButton:disabled {{ background: {tokens.BG_ACCENT_DISABLED};"
    f" color: {tokens.TEXT_MUTED}; }}"
)

_FONT = QFont(tokens.FONT_FAMILY.split(",")[0].strip(), tokens.FONT_SIZE_MD)


class InputRow(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask anything…")
        self._input.setFont(_FONT)
        self._input.setStyleSheet(_INPUT_STYLE)
        self._input.returnPressed.connect(self._on_submit)

        self._button = QPushButton("↵")
        self._button.setFixedSize(36, 36)
        self._button.setStyleSheet(_BUTTON_STYLE)
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
        self.setMinimumHeight(100)
        self.setFont(
            QFont(tokens.FONT_FAMILY.split(",")[0].strip(), tokens.FONT_SIZE_MD)
        )
        self.setStyleSheet(_RESPONSE_STYLE)

    def show_response(self, text: str) -> None:
        self.setStyleSheet(_RESPONSE_STYLE)
        self.setPlainText(text)

    def show_error(self, text: str) -> None:
        self.setStyleSheet(_RESPONSE_ERROR_STYLE)
        self.setPlainText(text)
