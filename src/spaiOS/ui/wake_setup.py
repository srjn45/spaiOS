from __future__ import annotations

from enum import Enum, auto

from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from spaiOS.core.wake_profile import WakePhrase, load_profile, save_profile
from spaiOS.core.wake_trainer import (
    calibrate_whisper_target,
    negative_dir,
    phrase_slug,
    positive_dir,
)
from spaiOS.core.voice import WakeSampleThread, save_wav
from spaiOS.ui import tokens

_POS_SAMPLES = 5
_NEG_SAMPLES = 3

_OWW_COMPATIBLE = {"hi spai", "hey spai", "hey jarvis", "alexa", "hey mycroft"}


def assign_wake_mode(phrase: str) -> str:
    return "oww_whisper" if phrase.lower() in _OWW_COMPATIBLE else "whisper_poll"


class _Step(Enum):
    CHOICE = auto()
    PHRASE_INPUT = auto()
    RECORDING_POS = auto()
    RECORDING_NEG = auto()
    CALIBRATING = auto()
    DONE = auto()


class _CalibThread(QThread):
    done = pyqtSignal(str)

    def __init__(self, recordings: list) -> None:
        super().__init__()
        self._recordings = recordings

    def run(self) -> None:
        target = calibrate_whisper_target(self._recordings)
        self.done.emit(target)


class WakeSetupDialog(QDialog):
    setup_complete = pyqtSignal(object)  # WakeProfile

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._step = _Step.CHOICE
        self._phrase = ""
        self._pos_recordings: list = []
        self._neg_recordings: list = []
        self._sample_thread: WakeSampleThread | None = None
        self._calib_thread: _CalibThread | None = None
        self._build_ui()
        self._show_choice()

    def _build_ui(self) -> None:
        self.setWindowTitle("Wake Word Setup")
        self.setFixedSize(420, 280)
        self.setStyleSheet(
            f"background: {tokens.BG_WINDOW}; color: white; font-size: 14px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        self._label = QLabel()
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._rb_hi_spai = QRadioButton("Use 'Hi Spai'  (recommended)")
        self._rb_custom = QRadioButton("Choose my own phrase")
        self._rb_hi_spai.setChecked(True)
        self._rb_group = QButtonGroup()
        self._rb_group.addButton(self._rb_hi_spai)
        self._rb_group.addButton(self._rb_custom)
        layout.addWidget(self._rb_hi_spai)
        layout.addWidget(self._rb_custom)

        self._phrase_input = QLineEdit()
        self._phrase_input.setPlaceholderText("Type your trigger phrase…")
        self._phrase_input.hide()
        layout.addWidget(self._phrase_input)

        self._btn = QPushButton("Next")
        self._btn.clicked.connect(self._on_next)
        layout.addWidget(self._btn)

    def _show_choice(self) -> None:
        self._rb_hi_spai.show()
        self._rb_custom.show()
        self._phrase_input.hide()
        self._label.setText("Choose how you want to trigger spaiOS:")
        self._btn.setText("Next")
        self._btn.setEnabled(True)

    def _on_next(self) -> None:
        if self._step == _Step.CHOICE:
            if self._rb_custom.isChecked():
                self._step = _Step.PHRASE_INPUT
                self._rb_hi_spai.hide()
                self._rb_custom.hide()
                self._phrase_input.show()
                self._label.setText(
                    "Type the exact phrase you want to use as your trigger:"
                )
                self._btn.setText("Start Recording")
            else:
                self._phrase = "hi spai"
                self._rb_hi_spai.hide()
                self._rb_custom.hide()
                self._start_pos_recording()

        elif self._step == _Step.PHRASE_INPUT:
            text = self._phrase_input.text().strip().lower()
            if not text:
                return
            self._phrase = text
            self._phrase_input.hide()
            self._start_pos_recording()

    def _start_pos_recording(self) -> None:
        self._step = _Step.RECORDING_POS
        self._pos_recordings = []
        self._record_next_positive()

    def _record_next_positive(self) -> None:
        n = len(self._pos_recordings) + 1
        self._label.setText(
            f"Say  '{self._phrase}'  clearly.\n\n"
            f"Recording {n} of {_POS_SAMPLES} in 1 second…"
        )
        self._btn.setEnabled(False)
        QTimer.singleShot(1000, self._do_record_positive)

    def _do_record_positive(self) -> None:
        n = len(self._pos_recordings) + 1
        self._label.setText(
            f"Listening…  say  '{self._phrase}'  now.\n\nTake {n} of {_POS_SAMPLES}"
        )
        self._sample_thread = WakeSampleThread()
        self._sample_thread.done.connect(self._on_positive_sample)
        self._sample_thread.start()

    def _on_positive_sample(self, audio) -> None:
        self._pos_recordings.append(audio)
        if len(self._pos_recordings) < _POS_SAMPLES:
            self._record_next_positive()
        else:
            self._start_neg_recording()

    def _start_neg_recording(self) -> None:
        self._step = _Step.RECORDING_NEG
        self._neg_recordings = []
        self._record_next_negative()

    def _record_next_negative(self) -> None:
        n = len(self._neg_recordings) + 1
        self._label.setText(
            f"Now say something else  (e.g. count to five).\n\n"
            f"Recording {n} of {_NEG_SAMPLES} in 1 second…"
        )
        QTimer.singleShot(1000, self._do_record_negative)

    def _do_record_negative(self) -> None:
        n = len(self._neg_recordings) + 1
        self._label.setText(
            f"Listening…  say anything EXCEPT  '{self._phrase}'.\n\nTake {n} of {_NEG_SAMPLES}"
        )
        self._sample_thread = WakeSampleThread()
        self._sample_thread.done.connect(self._on_negative_sample)
        self._sample_thread.start()

    def _on_negative_sample(self, audio) -> None:
        self._neg_recordings.append(audio)
        if len(self._neg_recordings) < _NEG_SAMPLES:
            self._record_next_negative()
        else:
            self._calibrate()

    def _calibrate(self) -> None:
        self._step = _Step.CALIBRATING
        self._label.setText("Calibrating accent… this takes a few seconds.")
        self._btn.setEnabled(False)
        self._calib_thread = _CalibThread(self._pos_recordings)
        self._calib_thread.done.connect(self._on_calibration_done)
        self._calib_thread.start()

    def _on_calibration_done(self, target: str) -> None:
        effective_target = target or self._phrase
        mode = assign_wake_mode(self._phrase)
        new_phrase = WakePhrase(
            phrase=self._phrase, mode=mode, whisper_target=effective_target
        )
        slug = phrase_slug(self._phrase)
        for i, audio in enumerate(self._pos_recordings):
            save_wav(audio, positive_dir(slug) / f"pos_{i:02d}.wav")
        for i, audio in enumerate(self._neg_recordings):
            save_wav(audio, negative_dir(slug) / f"neg_{i:02d}.wav")

        profile = load_profile()
        profile.phrases = [p for p in profile.phrases if p.phrase != self._phrase]
        profile.phrases.append(new_phrase)
        save_profile(profile)

        self._step = _Step.DONE
        self._label.setText(
            f"Done!  '{self._phrase}'  is now a trigger.\n\n"
            f"spaiOS heard: '{effective_target}'"
        )
        self._btn.setText("Close")
        self._btn.setEnabled(True)
        self._btn.clicked.disconnect()
        self._btn.clicked.connect(self.accept)
        self.setup_complete.emit(profile)
