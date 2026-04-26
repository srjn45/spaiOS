from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout

from spaiOS.core.orchestrator import AskThread
from spaiOS.ui import tokens
from spaiOS.ui.components import InputRow, ResponseView
from spaiOS.ui.neural_sphere import NeuralSphere

_FADE_MS = 200


class Overlay(QMainWindow):
    WIDTH = 480
    HEIGHT = 540

    def __init__(self) -> None:
        super().__init__()
        self._active_thread: AskThread | None = None
        self._fade_in: QPropertyAnimation | None = None
        self._build_window()
        self._center_on_screen()

    def _build_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(
            f"#container {{ background: {tokens.BG_WINDOW}; border-radius: 22px; }}"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        self._sphere = NeuralSphere()
        layout.addWidget(self._sphere)

        self._input_row = InputRow()
        self._input_row.submitted.connect(self._on_prompt_submitted)
        layout.addWidget(self._input_row)

        self._response_view = ResponseView()
        layout.addWidget(self._response_view)

        self.setCentralWidget(container)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = (geom.width() - self.WIDTH) // 2 + geom.x()
        y = (geom.height() - self.HEIGHT) // 2 + geom.y()
        self.move(x, y)

    def _start_fade_in(self) -> None:
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(_FADE_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_in = anim

    @pyqtSlot()
    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            super().show()
            self._start_fade_in()
            self.raise_()
            self.activateWindow()
            self._input_row.focus()

    def _on_prompt_submitted(self, prompt: str) -> None:
        self._input_row.set_enabled(False)
        self._response_view.clear()
        self._sphere.set_state("thinking")

        self._active_thread = AskThread(prompt)
        self._active_thread.result.connect(self._on_result)
        self._active_thread.error.connect(self._on_error)
        self._active_thread.finished.connect(self._on_thread_finished)
        self._active_thread.start()

    def _on_result(self, text: str) -> None:
        self._sphere.set_state("responding")
        self._response_view.show_response(text)
        self._input_row.clear()
        QTimer.singleShot(2000, lambda: self._sphere.set_state("idle"))

    def _on_error(self, msg: str) -> None:
        self._sphere.set_state("idle")
        self._response_view.show_error(msg)

    def _on_thread_finished(self) -> None:
        self._input_row.set_enabled(True)
        self._input_row.focus()
        self._active_thread = None

    def _cancel_thinking(self) -> None:
        if self._active_thread is not None:
            try:
                self._active_thread.result.disconnect(self._on_result)
                self._active_thread.error.disconnect(self._on_error)
                self._active_thread.finished.disconnect(self._on_thread_finished)
            except RuntimeError:
                pass
            self._active_thread = None
        self._sphere.set_state("idle")
        self._input_row.set_enabled(True)
        self._input_row.focus()

    def keyPressEvent(self, event: QEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            if self._active_thread is not None:
                self._cancel_thinking()
            else:
                self.hide()
        else:
            super().keyPressEvent(event)
