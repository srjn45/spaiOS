from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

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

_RESPONSE_QUESTION_STYLE = (
    f"QTextEdit {{ background: rgba(255, 175, 50, 12); border: 1px solid rgba(255, 175, 50, 100);"
    f" border-radius: 8px; color: rgba(255, 210, 130, 220);"
    f" padding: 10px 12px; font-size: {tokens.FONT_SIZE_MD}px; }}"
)

_BUTTON_STYLE = (
    f"QPushButton {{ background: {tokens.BG_ACCENT}; border: none; border-radius: 8px;"
    f" color: white; font-size: {tokens.FONT_SIZE_LG}px; }}"
    f"QPushButton:hover {{ background: {tokens.BG_ACCENT_HOVER}; }}"
    f"QPushButton:disabled {{ background: {tokens.BG_ACCENT_DISABLED};"
    f" color: {tokens.TEXT_MUTED}; }}"
)

_CAM_STYLE_OFF = (
    f"QPushButton {{ background: {tokens.BG_SURFACE}; border: 1px solid {tokens.BORDER_SUBTLE};"
    f" border-radius: 8px; color: {tokens.TEXT_MUTED}; font-size: {tokens.FONT_SIZE_LG}px; }}"
    f"QPushButton:hover {{ border-color: {tokens.BORDER_FOCUS}; color: {tokens.TEXT_PRIMARY}; }}"
)

_CAM_STYLE_ON = (
    f"QPushButton {{ background: rgba(140,120,255,60); border: 1px solid {tokens.BORDER_FOCUS};"
    f" border-radius: 8px; color: {tokens.TEXT_PRIMARY}; font-size: {tokens.FONT_SIZE_LG}px; }}"
    f"QPushButton:hover {{ background: rgba(140,120,255,90); }}"
)

_SHOW_MORE_STYLE = (
    f"QPushButton {{ background: transparent; border: none;"
    f" color: {tokens.TEXT_MUTED}; font-size: {tokens.FONT_SIZE_SM}px;"
    f" text-align: left; padding: 2px 0; }}"
    f"QPushButton:hover {{ color: {tokens.TEXT_PRIMARY}; }}"
)

_TRUNCATE_CHARS = 380

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

        self._cam_button = QPushButton("◉")
        self._cam_button.setFixedSize(36, 36)
        self._cam_button.setStyleSheet(_CAM_STYLE_OFF)
        self._cam_button.setToolTip("Toggle screen capture")
        self._cam_button.clicked.connect(self._on_cam_toggle)
        self._cam_active = False

        self._button = QPushButton("↵")
        self._button.setFixedSize(36, 36)
        self._button.setStyleSheet(_BUTTON_STYLE)
        self._button.clicked.connect(self._on_submit)

        layout.addWidget(self._input)
        layout.addWidget(self._cam_button)
        layout.addWidget(self._button)

    def _on_cam_toggle(self) -> None:
        self._cam_active = not self._cam_active
        self._cam_button.setStyleSheet(
            _CAM_STYLE_ON if self._cam_active else _CAM_STYLE_OFF
        )

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self.submitted.emit(text)

    @property
    def camera_active(self) -> bool:
        return self._cam_active

    def set_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._button.setEnabled(enabled)
        self._cam_button.setEnabled(enabled)

    def clear(self) -> None:
        self._input.clear()

    def focus(self) -> None:
        self._input.setFocus()

    def set_placeholder(self, text: str) -> None:
        self._input.setPlaceholderText(text)


class ResponseView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setMinimumHeight(100)
        self._text.setFont(_FONT)
        self._text.setStyleSheet(_RESPONSE_STYLE)
        layout.addWidget(self._text)

        self._more_btn = QPushButton("Show more ↓")
        self._more_btn.setStyleSheet(_SHOW_MORE_STYLE)
        self._more_btn.hide()
        self._more_btn.clicked.connect(self._toggle_expand)
        layout.addWidget(self._more_btn)

        self._full_text = ""
        self._expanded = False

    def _set_content(self, text: str, style: str) -> None:
        self._text.setStyleSheet(style)
        self._full_text = text
        self._expanded = False
        if len(text) > _TRUNCATE_CHARS:
            self._text.setPlainText(text[:_TRUNCATE_CHARS] + "…")
            self._more_btn.setText("Show more ↓")
            self._more_btn.show()
        else:
            self._text.setPlainText(text)
            self._more_btn.hide()

    def _toggle_expand(self) -> None:
        if self._expanded:
            self._text.setPlainText(self._full_text[:_TRUNCATE_CHARS] + "…")
            self._more_btn.setText("Show more ↓")
            self._expanded = False
        else:
            self._text.setPlainText(self._full_text)
            self._more_btn.setText("Show less ↑")
            self._expanded = True

    def show_response(self, text: str) -> None:
        self._set_content(text, _RESPONSE_STYLE)

    def show_question(self, text: str) -> None:
        self._set_content(text, _RESPONSE_QUESTION_STYLE)

    def show_error(self, text: str) -> None:
        self._text.setStyleSheet(_RESPONSE_ERROR_STYLE)
        self._full_text = text
        self._text.setPlainText(text)
        self._more_btn.hide()
        self._expanded = False

    def clear(self) -> None:
        self._text.clear()
        self._more_btn.hide()
        self._full_text = ""
        self._expanded = False
