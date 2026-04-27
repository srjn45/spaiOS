import numpy as np
from PyQt6.QtCore import QEasingCurve, QEvent, QPropertyAnimation, Qt, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
)

from spaiOS.core.orchestrator import AskThread, AskWithVisionThread, Orchestrator
from spaiOS.core.orchestrator import is_clarifying_question
from spaiOS.core.screen_capture import capture_jpeg
from spaiOS.core.voice import (
    AudioTranscribeThread,
    VoiceRecorder,
    VoiceTranscribeThread,
)
from spaiOS.ui import tokens
from spaiOS.ui.components import InputRow, ResponseView
from spaiOS.ui.neural_sphere import NeuralSphere

_FADE_MS = 200
_IDLE_DISMISS_MS = 30_000  # hide after 30s of no activity


class Overlay(QMainWindow):
    WIDTH = 480
    HEIGHT = 540

    def __init__(self) -> None:
        super().__init__()
        self._orchestrator = Orchestrator()
        self._active_thread: AskThread | AskWithVisionThread | None = None
        self._voice_recorder = VoiceRecorder()
        self._voice_thread: VoiceTranscribeThread | AudioTranscribeThread | None = None
        self._fade_in: QPropertyAnimation | None = None
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(_IDLE_DISMISS_MS)
        self._idle_timer.timeout.connect(self._on_idle_timeout)
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

        # mic indicator: small dot shown when wake word listener is active
        self._mic_dot = QLabel("⬤")
        self._mic_dot.setStyleSheet(
            "color: rgba(60, 220, 130, 180); font-size: 8px; padding: 0;"
        )
        self._mic_dot.setToolTip("Wake word listener active")
        self._mic_dot.hide()
        dot_row = QHBoxLayout()
        dot_row.addStretch()
        dot_row.addWidget(self._mic_dot)
        layout.addLayout(dot_row)

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

    def _reset_idle_timer(self) -> None:
        if self.isVisible():
            self._idle_timer.start()

    def _on_idle_timeout(self) -> None:
        if self._active_thread is None and self._voice_thread is None:
            self._orchestrator.clear_history()
            self.hide()

    @pyqtSlot()
    def toggle(self) -> None:
        if self.isVisible():
            self._orchestrator.clear_history()
            self._idle_timer.stop()
            self.hide()
        else:
            super().show()
            self._start_fade_in()
            self.raise_()
            self.activateWindow()
            self._input_row.focus()
            self._reset_idle_timer()

    def _on_prompt_submitted(self, prompt: str) -> None:
        self._idle_timer.stop()

        if prompt.strip().lower() == "/clear":
            self._orchestrator.clear_history()
            self._input_row.clear()
            self._input_row.set_placeholder("Ask anything…")
            self._response_view.show_response("Context cleared — starting fresh.")
            self._input_row.set_enabled(True)
            self._input_row.focus()
            self._reset_idle_timer()
            return

        self._input_row.set_enabled(False)
        self._input_row.set_placeholder("Ask anything…")
        self._response_view.clear()
        self._sphere.set_state("thinking")

        if self._input_row.camera_active:
            try:
                image_bytes = capture_jpeg()
            except Exception as exc:
                self._on_error(f"Screen capture failed: {exc}")
                self._input_row.set_enabled(True)
                self._input_row.focus()
                return
            thread: AskThread | AskWithVisionThread = AskWithVisionThread(
                prompt, image_bytes
            )
        else:
            thread = AskThread(prompt, self._orchestrator)

        self._active_thread = thread
        self._active_thread.result.connect(self._on_result)
        self._active_thread.error.connect(self._on_error)
        self._active_thread.finished.connect(self._on_thread_finished)
        self._active_thread.start()

    def _on_result(self, text: str) -> None:
        self._input_row.clear()
        if is_clarifying_question(text):
            self._sphere.set_state("questioning")
            self._response_view.show_question(text)
            self._input_row.set_placeholder("Your answer…")
        else:
            self._sphere.set_state("responding")
            self._response_view.show_response(text)
            QTimer.singleShot(2000, lambda: self._sphere.set_state("idle"))
        self._reset_idle_timer()

    def _on_error(self, msg: str) -> None:
        self._sphere.set_state("idle")
        self._response_view.show_error(msg)
        self._reset_idle_timer()

    def _on_thread_finished(self) -> None:
        self._input_row.set_enabled(True)
        self._input_row.focus()
        self._active_thread = None

    @pyqtSlot()
    def toggle_voice(self) -> None:
        if self._voice_recorder.is_recording:
            self._sphere.set_state("thinking")
            self._response_view.show_response("Transcribing…")
            thread = VoiceTranscribeThread(self._voice_recorder)
            self._voice_thread = thread
            thread.result.connect(self._on_voice_result)
            thread.error.connect(self._on_voice_error)
            thread.finished.connect(self._on_voice_thread_done)
            thread.start()
        else:
            if self._active_thread is not None:
                return
            try:
                self._voice_recorder.start()
            except Exception as exc:
                self._on_error(f"Microphone error: {exc}")
                return
            self._sphere.set_state("listening")
            self._response_view.show_response(
                "Listening… press Super+Shift+Space again to stop"
            )
            self._input_row.set_enabled(False)

    def _on_voice_result(self, text: str) -> None:
        if not text.strip():
            self._sphere.set_state("idle")
            self._response_view.show_error("No speech detected — try again.")
            self._input_row.set_enabled(True)
            self._input_row.focus()
            self._reset_idle_timer()
            return
        self._on_prompt_submitted(text)

    def _on_voice_error(self, msg: str) -> None:
        self._sphere.set_state("idle")
        self._response_view.show_error(msg)
        self._input_row.set_enabled(True)
        self._input_row.focus()
        self._reset_idle_timer()

    def _on_voice_thread_done(self) -> None:
        self._voice_thread = None

    def set_wake_listener_active(self, active: bool) -> None:
        if active:
            self._mic_dot.show()
        else:
            self._mic_dot.hide()

    @pyqtSlot()
    def on_wake_word(self) -> None:
        if not self.isVisible():
            super().show()
            self._start_fade_in()
            self.raise_()
            self.activateWindow()
        self._idle_timer.stop()
        self._sphere.set_state("listening")
        self._response_view.show_response(
            "Listening… speak now (auto-transcribes in 6s)"
        )
        self._input_row.set_enabled(False)

    @pyqtSlot(object, object)
    def on_wake_audio_ready(self, audio: object, noise_profile: object) -> None:
        print(f"[spaiOS] on_wake_audio_ready received, type={type(audio)}")
        if not isinstance(audio, np.ndarray):
            return
        profile = noise_profile if isinstance(noise_profile, np.ndarray) else None
        self._sphere.set_state("thinking")
        self._response_view.show_response("Transcribing…")
        thread = AudioTranscribeThread(audio, profile)
        self._voice_thread = thread
        thread.result.connect(self._on_voice_result)
        thread.error.connect(self._on_voice_error)
        thread.finished.connect(self._on_voice_thread_done)
        thread.start()

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
        self._reset_idle_timer()

    def keyPressEvent(self, event: QEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            if self._active_thread is not None:
                self._cancel_thinking()
            else:
                self._orchestrator.clear_history()
                self._idle_timer.stop()
                self.hide()
        else:
            super().keyPressEvent(event)
