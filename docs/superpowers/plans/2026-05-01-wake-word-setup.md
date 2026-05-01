# Wake Word Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users record a custom wake phrase ("Hi Spai" or any phrase) by speaking it 5 times; spaiOS calibrates what Whisper hears for their accent and stores it so the phrase reliably triggers the overlay.

**Architecture:** Two detection paths co-exist in `WakeWordListener`. OWW-compatible phrases ("hi spai", "hey jarvis") continue to use the existing openWakeWord detector. Fully custom phrases ("cutto", etc.) are detected by `WhisperPollThread`, which reads from a shared audio queue filled by the OWW loop, transcribes 3-second windows every ~3 seconds, and fuzzy-matches against stored targets. A `WakeSetupDialog` wizard walks the user through recording 5 samples, runs Whisper calibration to learn the user's accent, and saves the result to `~/.local/share/spaiOS/wake_profile.json`.

**Tech Stack:** PyQt6 (dialog UI), openWakeWord (OWW path), faster-whisper (calibration + poll path), Python stdlib `wave` (WAV I/O), `difflib.SequenceMatcher` (fuzzy match), `queue.Queue` (audio hand-off between threads)

---

## File Map

| File | Status | Responsibility |
|------|--------|----------------|
| `src/spaiOS/core/wake_profile.py` | CREATE | `WakePhrase`/`WakeProfile` dataclasses, `load_profile`, `save_profile` |
| `src/spaiOS/core/wake_trainer.py` | CREATE | `calibrate_whisper_target`, `phrase_slug`, `positive_dir`, `negative_dir` |
| `src/spaiOS/ui/wake_setup.py` | CREATE | `WakeSetupDialog` wizard + `assign_wake_mode` helper |
| `src/spaiOS/core/voice.py` | MODIFY | Add `save_wav`, `WakeSampleThread`, `_fuzzy_match`, `WhisperPollThread`; update `WakeWordListener` |
| `src/spaiOS/ui/overlay.py` | MODIFY | Handle `/wake-setup` command; add `on_poll_wake_word` slot |
| `src/spaiOS/main.py` | MODIFY | Connect `WakeWordListener.poll_wake` to `overlay.on_poll_wake_word` |
| `tests/test_wake_profile.py` | CREATE | Profile load/save tests |
| `tests/test_wake_trainer.py` | CREATE | Calibration + slug helper tests |
| `tests/test_wake_setup.py` | CREATE | `assign_wake_mode` tests; dialog smoke test |
| `tests/test_voice.py` | MODIFY | Add `save_wav` + `_fuzzy_match` tests |

---

## Task 1: WakeProfileStore

**Files:**
- Create: `src/spaiOS/core/wake_profile.py`
- Create: `tests/test_wake_profile.py`

- [ ] **Step 1.1: Write failing tests**

```python
# tests/test_wake_profile.py
import json
from pathlib import Path

import pytest

from spaiOS.core.wake_profile import WakePhrase, WakeProfile, load_profile, save_profile


def test_default_profile_has_hey_jarvis():
    p = WakeProfile()
    assert len(p.phrases) == 1
    assert p.phrases[0].phrase == "hey jarvis"
    assert p.phrases[0].mode == "hey_jarvis_compat"
    assert p.phrases[0].whisper_target is None


def test_load_profile_returns_default_when_no_file(tmp_path, monkeypatch):
    import spaiOS.core.wake_profile as wp_mod
    monkeypatch.setattr(wp_mod, "_PROFILE_PATH", tmp_path / "wake_profile.json")
    p = load_profile()
    assert p.phrases[0].phrase == "hey jarvis"


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    import spaiOS.core.wake_profile as wp_mod
    monkeypatch.setattr(wp_mod, "_PROFILE_PATH", tmp_path / "wake_profile.json")
    original = WakeProfile(phrases=[
        WakePhrase("hi spai", "oww_whisper", whisper_target="hi spy"),
        WakePhrase("cutto", "whisper_poll", whisper_target="kato"),
    ])
    save_profile(original)
    loaded = load_profile()
    assert len(loaded.phrases) == 2
    assert loaded.phrases[0].phrase == "hi spai"
    assert loaded.phrases[0].whisper_target == "hi spy"
    assert loaded.phrases[1].mode == "whisper_poll"
    assert loaded.phrases[1].whisper_target == "kato"


def test_save_creates_parent_directories(tmp_path, monkeypatch):
    import spaiOS.core.wake_profile as wp_mod
    path = tmp_path / "nested" / "dir" / "wake_profile.json"
    monkeypatch.setattr(wp_mod, "_PROFILE_PATH", path)
    save_profile(WakeProfile())
    assert path.exists()


def test_load_handles_missing_whisper_target(tmp_path, monkeypatch):
    import spaiOS.core.wake_profile as wp_mod
    path = tmp_path / "wake_profile.json"
    monkeypatch.setattr(wp_mod, "_PROFILE_PATH", path)
    path.write_text(json.dumps({"phrases": [
        {"phrase": "hey jarvis", "mode": "hey_jarvis_compat", "whisper_target": None}
    ]}))
    p = load_profile()
    assert p.phrases[0].whisper_target is None
```

- [ ] **Step 1.2: Run tests to confirm they fail**

```bash
cd /home/srajan/Development/spaiOS
uv run pytest tests/test_wake_profile.py -v
```
Expected: `ModuleNotFoundError: No module named 'spaiOS.core.wake_profile'`

- [ ] **Step 1.3: Write the implementation**

```python
# src/spaiOS/core/wake_profile.py
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

_PROFILE_PATH = Path.home() / ".local" / "share" / "spaiOS" / "wake_profile.json"


@dataclass
class WakePhrase:
    phrase: str
    mode: str  # "hey_jarvis_compat" | "oww_whisper" | "whisper_poll"
    whisper_target: str | None = None


@dataclass
class WakeProfile:
    phrases: list[WakePhrase] = field(
        default_factory=lambda: [WakePhrase("hey jarvis", "hey_jarvis_compat")]
    )


def load_profile() -> WakeProfile:
    if not _PROFILE_PATH.exists():
        return WakeProfile()
    with open(_PROFILE_PATH) as f:
        raw = json.load(f)
    phrases = [WakePhrase(**p) for p in raw.get("phrases", [])]
    return WakeProfile(phrases=phrases) if phrases else WakeProfile()


def save_profile(profile: WakeProfile) -> None:
    _PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_PROFILE_PATH, "w") as f:
        json.dump({"phrases": [asdict(p) for p in profile.phrases]}, f, indent=2)
```

- [ ] **Step 1.4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_wake_profile.py -v
```
Expected: 5 PASSED

- [ ] **Step 1.5: Commit**

```bash
git add src/spaiOS/core/wake_profile.py tests/test_wake_profile.py
git commit -m "Add WakeProfileStore with load/save and default hey-jarvis entry"
```

---

## Task 2: WAV I/O + WakeSampleThread

**Files:**
- Modify: `src/spaiOS/core/voice.py` (add `save_wav`, `WakeSampleThread`)
- Modify: `tests/test_voice.py` (add new tests at the bottom)

- [ ] **Step 2.1: Write failing tests**

Add to the bottom of `tests/test_voice.py`:

```python
# ── save_wav ──────────────────────────────────────────────────────────────────


def test_save_wav_creates_file(tmp_path):
    from spaiOS.core.voice import save_wav
    audio = np.zeros(16000, dtype=np.float32)
    path = tmp_path / "test.wav"
    save_wav(audio, path)
    assert path.exists()


def test_save_wav_correct_format(tmp_path):
    import wave
    from spaiOS.core.voice import save_wav
    audio = np.zeros(16000, dtype=np.float32)
    path = tmp_path / "test.wav"
    save_wav(audio, path)
    with wave.open(str(path), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 16000
        assert wf.getnframes() == 16000


def test_save_wav_clips_amplitude(tmp_path):
    import wave
    from spaiOS.core.voice import save_wav
    audio = np.array([2.0, -2.0, 0.5], dtype=np.float32)
    path = tmp_path / "clip.wav"
    save_wav(audio, path)
    with wave.open(str(path), "rb") as wf:
        pcm = np.frombuffer(wf.readframes(3), dtype=np.int16)
    assert pcm[0] == 32767
    assert pcm[1] == -32767
    assert abs(pcm[2] - 16383) <= 1


def test_save_wav_creates_parent_dirs(tmp_path):
    from spaiOS.core.voice import save_wav
    path = tmp_path / "nested" / "dir" / "out.wav"
    save_wav(np.zeros(1600, dtype=np.float32), path)
    assert path.exists()
```

- [ ] **Step 2.2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_voice.py::test_save_wav_creates_file -v
```
Expected: `ImportError: cannot import name 'save_wav' from 'spaiOS.core.voice'`

- [ ] **Step 2.3: Add `save_wav` and `WakeSampleThread` to `voice.py`**

Add `import wave` to the imports at the top of `src/spaiOS/core/voice.py`.

Then add these two items after the `VoiceTranscribeThread` class (around line 161):

```python
def save_wav(audio: np.ndarray, path: Path) -> None:
    """Save float32 mono 16kHz audio as 16-bit PCM WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())


class WakeSampleThread(QThread):
    """Records a single 2-second audio clip at 16 kHz mono."""

    done = pyqtSignal(object)  # emits np.ndarray

    def run(self) -> None:
        audio = sd.rec(
            2 * _SAMPLE_RATE,
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype="float32",
        )
        sd.wait()
        self.done.emit(audio.flatten().copy())
```

- [ ] **Step 2.4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_voice.py -v
```
Expected: all previous tests + 4 new PASSED (total increases by 4)

- [ ] **Step 2.5: Commit**

```bash
git add src/spaiOS/core/voice.py tests/test_voice.py
git commit -m "Add save_wav helper and WakeSampleThread to voice module"
```

---

## Task 3: Whisper Calibration (wake_trainer.py)

**Files:**
- Create: `src/spaiOS/core/wake_trainer.py`
- Create: `tests/test_wake_trainer.py`

- [ ] **Step 3.1: Write failing tests**

```python
# tests/test_wake_trainer.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from spaiOS.core.wake_trainer import (
    calibrate_whisper_target,
    negative_dir,
    phrase_slug,
    positive_dir,
)


def test_phrase_slug_spaces():
    assert phrase_slug("hi spai") == "hi_spai"


def test_phrase_slug_uppercase():
    assert phrase_slug("Cutto") == "cutto"


def test_phrase_slug_apostrophe():
    assert phrase_slug("hey it's me") == "hey_its_me"


def test_positive_dir_path():
    path = positive_dir("hi_spai")
    assert path.parts[-1] == "positive"
    assert path.parts[-2] == "hi_spai"
    assert "wake-samples" in str(path)


def test_negative_dir_path():
    path = negative_dir("hi_spai")
    assert path.parts[-1] == "negative"
    assert path.parts[-2] == "hi_spai"


def test_calibrate_returns_most_common_transcription():
    with patch("spaiOS.core.wake_trainer._get_whisper_model") as mock_fn:
        mock_model = MagicMock()
        # 3 × "hi spy", 2 × "hi space" — "hi spy" wins
        mock_model.transcribe.side_effect = [
            ([MagicMock(text="hi spy")], None),
            ([MagicMock(text="hi spy")], None),
            ([MagicMock(text="hi space")], None),
            ([MagicMock(text="hi spy")], None),
            ([MagicMock(text="hi space")], None),
        ]
        mock_fn.return_value = mock_model
        recordings = [np.zeros(32000, dtype=np.float32) for _ in range(5)]
        result = calibrate_whisper_target(recordings)
    assert result == "hi spy"


def test_calibrate_returns_empty_for_no_recordings():
    assert calibrate_whisper_target([]) == ""


def test_calibrate_strips_and_lowercases():
    with patch("spaiOS.core.wake_trainer._get_whisper_model") as mock_fn:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([MagicMock(text="  Hi Spai  ")], None)
        mock_fn.return_value = mock_model
        result = calibrate_whisper_target([np.zeros(32000, dtype=np.float32)])
    assert result == "hi spai"
```

- [ ] **Step 3.2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_wake_trainer.py -v
```
Expected: `ModuleNotFoundError: No module named 'spaiOS.core.wake_trainer'`

- [ ] **Step 3.3: Write the implementation**

```python
# src/spaiOS/core/wake_trainer.py
from collections import Counter
from pathlib import Path

import numpy as np

from spaiOS.core.voice import _get_whisper_model, _SAMPLE_RATE

_WAKE_SAMPLES_DIR = Path.home() / ".local" / "share" / "spaiOS" / "wake-samples"


def phrase_slug(phrase: str) -> str:
    return phrase.lower().replace(" ", "_").replace("'", "")


def positive_dir(slug: str) -> Path:
    return _WAKE_SAMPLES_DIR / slug / "positive"


def negative_dir(slug: str) -> Path:
    return _WAKE_SAMPLES_DIR / slug / "negative"


def calibrate_whisper_target(recordings: list[np.ndarray]) -> str:
    if not recordings:
        return ""
    model = _get_whisper_model()
    results = []
    for audio in recordings:
        segments, _ = model.transcribe(audio, language="en")
        text = " ".join(seg.text.strip() for seg in segments).strip().lower()
        results.append(text)
    return Counter(results).most_common(1)[0][0]
```

- [ ] **Step 3.4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_wake_trainer.py -v
```
Expected: 7 PASSED

- [ ] **Step 3.5: Commit**

```bash
git add src/spaiOS/core/wake_trainer.py tests/test_wake_trainer.py
git commit -m "Add Whisper-based phrase calibration and WAV sample path helpers"
```

---

## Task 4: WakeSetupDialog

**Files:**
- Create: `src/spaiOS/ui/wake_setup.py`
- Create: `tests/test_wake_setup.py`

- [ ] **Step 4.1: Write failing tests**

These tests cover the unit-testable logic (`assign_wake_mode`) and a smoke test that the dialog constructs without crashing.

```python
# tests/test_wake_setup.py
import pytest


# ── assign_wake_mode ──────────────────────────────────────────────────────────

def test_hi_spai_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("hi spai") == "oww_whisper"


def test_hey_jarvis_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("hey jarvis") == "oww_whisper"


def test_alexa_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("alexa") == "oww_whisper"


def test_custom_phrase_is_whisper_poll():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("cutto") == "whisper_poll"
    assert assign_wake_mode("banana boat") == "whisper_poll"
    assert assign_wake_mode("start session") == "whisper_poll"


# ── dialog smoke test ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def qapp():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_wake_setup_dialog_constructs(qapp):
    from unittest.mock import patch
    with patch("spaiOS.ui.wake_setup.load_profile"), \
         patch("spaiOS.ui.wake_setup.save_profile"):
        from spaiOS.ui.wake_setup import WakeSetupDialog
        dlg = WakeSetupDialog()
        assert dlg.windowTitle() == "Wake Word Setup"
        dlg.destroy()
```

- [ ] **Step 4.2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_wake_setup.py -v
```
Expected: `ModuleNotFoundError: No module named 'spaiOS.ui.wake_setup'`

- [ ] **Step 4.3: Write the implementation**

```python
# src/spaiOS/ui/wake_setup.py
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

from spaiOS.core.wake_profile import WakePhrase, WakeProfile, load_profile, save_profile
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

# Phrases whose phonemes OWW (hey_jarvis base) will catch reliably.
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

    # ── step transitions ──────────────────────────────────────────────────────

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
            f"Listening…  say  '{self._phrase}'  now.\n\n"
            f"Take {n} of {_POS_SAMPLES}"
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
            f"Listening…  say anything EXCEPT  '{self._phrase}'.\n\n"
            f"Take {n} of {_NEG_SAMPLES}"
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
```

- [ ] **Step 4.4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_wake_setup.py -v
```
Expected: 6 PASSED

- [ ] **Step 4.5: Lint check**

```bash
uv run black src/spaiOS/ui/wake_setup.py --check
uv run flake8 src/spaiOS/ui/wake_setup.py --max-line-length=100
```
Expected: no errors (reformat with `uv run black src/spaiOS/ui/wake_setup.py` if needed).

- [ ] **Step 4.6: Commit**

```bash
git add src/spaiOS/ui/wake_setup.py tests/test_wake_setup.py
git commit -m "Add WakeSetupDialog: 5-sample recording wizard with Whisper accent calibration"
```

---

## Task 5: Multi-Phrase Detection + Overlay Wiring

**Files:**
- Modify: `src/spaiOS/core/voice.py` (add `_fuzzy_match`, `WhisperPollThread`; update `WakeWordListener`)
- Modify: `src/spaiOS/ui/overlay.py` (add `/wake-setup` command, `on_poll_wake_word` slot)
- Modify: `src/spaiOS/main.py` (connect `poll_wake` signal)
- Modify: `tests/test_voice.py` (add fuzzy match tests)

### 5a — `_fuzzy_match` + tests

- [ ] **Step 5.1: Write failing tests for `_fuzzy_match`**

Add to the bottom of `tests/test_voice.py`:

```python
# ── _fuzzy_match ──────────────────────────────────────────────────────────────


def test_fuzzy_match_exact():
    from spaiOS.core.voice import _fuzzy_match
    assert _fuzzy_match("hi spai", "hi spai") is True


def test_fuzzy_match_accent_variant():
    from spaiOS.core.voice import _fuzzy_match
    # "hi spy" should match "hi spai" (ratio ~0.77, above 0.6 threshold)
    assert _fuzzy_match("hi spy", "hi spai") is True


def test_fuzzy_match_phrase_in_longer_text():
    from spaiOS.core.voice import _fuzzy_match
    # "hey cutto" vs "cutto" → ratio ~0.71
    assert _fuzzy_match("hey cutto", "cutto") is True


def test_fuzzy_match_unrelated_text():
    from spaiOS.core.voice import _fuzzy_match
    assert _fuzzy_match("what is the weather", "cutto") is False


def test_fuzzy_match_case_insensitive():
    from spaiOS.core.voice import _fuzzy_match
    assert _fuzzy_match("Hi Spai", "hi spai") is True
```

- [ ] **Step 5.2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_voice.py::test_fuzzy_match_exact -v
```
Expected: `ImportError: cannot import name '_fuzzy_match'`

- [ ] **Step 5.3: Add `_fuzzy_match` to `voice.py`**

Add this function just before the `WakeWordListener` class in `src/spaiOS/core/voice.py`:

```python
def _fuzzy_match(text: str, target: str, threshold: float = 0.6) -> bool:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text.lower(), target.lower()).ratio() >= threshold
```

- [ ] **Step 5.4: Run fuzzy match tests**

```bash
uv run pytest tests/test_voice.py -k "fuzzy" -v
```
Expected: 5 PASSED

### 5b — `WhisperPollThread`

- [ ] **Step 5.5: Add `WhisperPollThread` to `voice.py`**

Add this class just after `_fuzzy_match` and before `WakeWordListener`:

```python
import queue as _queue


class WhisperPollThread(QThread):
    """Background Whisper-based phrase detection for non-OWW (whisper_poll) phrases.

    Reads int16 audio chunks from `audio_queue` (fed by WakeWordListener),
    transcribes every ~3 seconds, and emits `wake` with the matched phrase text.
    """

    wake = pyqtSignal(str)

    def __init__(self, phrases: list, audio_queue: _queue.Queue) -> None:
        super().__init__()
        self._phrases = phrases  # list[WakePhrase]
        self._queue = audio_queue
        self._running = False

    def run(self) -> None:
        import time

        self._running = True
        _chunks_per_3s = max(1, int(3 * _SAMPLE_RATE / _OWW_CHUNK))  # ≈ 37

        while self._running:
            buffer: list[np.ndarray] = []
            for _ in range(_chunks_per_3s):
                try:
                    chunk = self._queue.get(timeout=0.5)
                    buffer.append(chunk)
                except _queue.Empty:
                    if not self._running:
                        return

            if not buffer or not self._running:
                continue

            audio = np.concatenate(buffer).astype(np.float32) / 32768.0
            model = _get_whisper_model()
            segments, _ = model.transcribe(audio, language="en")
            text = " ".join(seg.text.strip() for seg in segments).strip().lower()

            for wp in self._phrases:
                target = wp.whisper_target or wp.phrase
                if target and _fuzzy_match(text, target):
                    self.wake.emit(wp.phrase)
                    while not self._queue.empty():
                        try:
                            self._queue.get_nowait()
                        except _queue.Empty:
                            break
                    time.sleep(2)
                    break

    def stop(self) -> None:
        self._running = False
        self.wait()
```

### 5c — Update `WakeWordListener`

- [ ] **Step 5.6: Update `WakeWordListener` to load profile + start poll thread**

In `src/spaiOS/core/voice.py`, update `WakeWordListener`:

Replace the existing `__init__` and `run` signature block (currently lines ~191–199):

```python
class WakeWordListener(QThread):
    wake = pyqtSignal()
    poll_wake = pyqtSignal()  # fired by WhisperPollThread for whisper_poll phrases
    audio_ready = pyqtSignal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._poll_thread: WhisperPollThread | None = None

    def _on_poll_wake(self, _phrase: str) -> None:
        self.poll_wake.emit()
```

At the top of `WakeWordListener.run()`, before the `from openwakeword...` import, add:

```python
    def run(self) -> None:
        from spaiOS.core.wake_profile import load_profile

        profile = load_profile()
        poll_phrases = [p for p in profile.phrases if p.mode == "whisper_poll"]

        poll_queue: _queue.Queue | None = None
        if poll_phrases:
            poll_queue = _queue.Queue(maxsize=200)
            self._poll_thread = WhisperPollThread(poll_phrases, poll_queue)
            self._poll_thread.wake.connect(self._on_poll_wake)
            self._poll_thread.start()

        # ... rest of existing run() body unchanged, EXCEPT:
        # inside the `while self._running:` loop, after `raw = bytes(data)`,
        # add the queue feed:
        #
        #   if poll_queue is not None and not in_utterance:
        #       try:
        #           poll_queue.put_nowait(pcm16)
        #       except _queue.Full:
        #           pass
```

The full updated `run()` method (replacing the entire existing one from line ~199):

```python
    def run(self) -> None:
        from spaiOS.core.wake_profile import load_profile

        profile = load_profile()
        poll_phrases = [p for p in profile.phrases if p.mode == "whisper_poll"]

        poll_queue: _queue.Queue | None = None
        if poll_phrases:
            poll_queue = _queue.Queue(maxsize=200)
            self._poll_thread = WhisperPollThread(poll_phrases, poll_queue)
            self._poll_thread.wake.connect(self._on_poll_wake)
            self._poll_thread.start()

        from openwakeword.model import Model
        import openwakeword

        model_dir = Path(openwakeword.__file__).parent / "resources" / "models"
        model_path = str(model_dir / f"{_WAKE_MODEL_NAME}.onnx")
        oww = Model(wakeword_model_paths=[model_path])
        vad = SileroVAD()
        _utterance_max = int(_UTTERANCE_MAX_S * _SAMPLE_RATE)

        self._running = True

        with sd.RawInputStream(
            samplerate=_SAMPLE_RATE,
            blocksize=_OWW_CHUNK,
            dtype="int16",
            channels=_CHANNELS,
        ) as stream:
            noise_frames: list[np.ndarray] = []
            noise_target = int(_NOISE_PROFILE_S * _SAMPLE_RATE / _OWW_CHUNK)
            print("[spaiOS] Calibrating ambient noise profile…")
            for _ in range(noise_target):
                data, _ = stream.read(_OWW_CHUNK)
                chunk = (
                    np.frombuffer(bytes(data), dtype="int16").astype(np.float32)
                    / 32768.0
                )
                noise_frames.append(chunk)
            noise_profile = np.concatenate(noise_frames)
            print("[spaiOS] Noise profile ready. Wake word listener active.")

            in_utterance = False
            utterance_frames: list[bytes] = []
            utterance_n = 0
            vad_buffer: list[float] = []
            silence_chunks = 0
            speech_detected = False
            max_prob = 0.0

            while self._running:
                data, _ = stream.read(_OWW_CHUNK)
                raw = bytes(data)
                pcm16 = np.frombuffer(raw, dtype="int16")

                # Feed whisper_poll thread when not mid-utterance
                if poll_queue is not None and not in_utterance:
                    try:
                        poll_queue.put_nowait(pcm16)
                    except _queue.Full:
                        pass

                if in_utterance:
                    utterance_frames.append(raw)
                    float_chunk = pcm16.astype(np.float32) / 32768.0
                    utterance_n += len(pcm16)
                    vad_buffer.extend(float_chunk.tolist())

                    while len(vad_buffer) >= _VAD_CHUNK:
                        window = np.array(vad_buffer[:_VAD_CHUNK], dtype=np.float32)
                        vad_buffer = vad_buffer[_VAD_CHUNK:]
                        prob = vad.predict(window)
                        rms = float(np.sqrt(np.mean(window**2)))
                        if prob >= _VAD_SPEECH_THRESHOLD:
                            speech_detected = True
                            silence_chunks = 0
                            max_prob = max(max_prob, prob)
                        elif speech_detected:
                            silence_chunks += 1
                        print(
                            f"[VAD] rms={rms:.3f} prob={prob:.2f} "
                            f"speech={speech_detected} sil={silence_chunks}/{_VAD_SILENCE_CHUNKS}",
                            end="\r",
                        )

                    end_by_vad = speech_detected and silence_chunks >= _VAD_SILENCE_CHUNKS
                    end_by_timeout = utterance_n >= _utterance_max

                    if end_by_vad or end_by_timeout:
                        reason = "VAD silence" if end_by_vad else "12s timeout"
                        audio = (
                            np.frombuffer(b"".join(utterance_frames), dtype="int16")
                            .astype(np.float32)
                            / 32768.0
                        )
                        print(
                            f"\n[spaiOS] utterance done ({reason}) — "
                            f"{len(audio)} samples, max_vad_prob={max_prob:.2f}"
                        )
                        self.audio_ready.emit(audio, noise_profile)
                        in_utterance = False
                        utterance_frames = []
                        utterance_n = 0
                        vad_buffer = []
                        silence_chunks = 0
                        speech_detected = False
                        max_prob = 0.0
                        vad.reset()
                        oww.reset()
                else:
                    prediction = oww.predict(pcm16)
                    score = prediction.get(_WAKE_MODEL_NAME, 0.0)
                    if score >= _WAKE_THRESHOLD:
                        print(f"[spaiOS] wake word detected (score={score:.2f})")
                        in_utterance = True
                        utterance_frames = []
                        utterance_n = 0
                        vad_buffer = []
                        silence_chunks = 0
                        speech_detected = False
                        max_prob = 0.0
                        vad.reset()
                        oww.reset()
                        self.wake.emit()

        if self._poll_thread is not None:
            self._poll_thread.stop()

    def stop(self) -> None:
        self._running = False
        self.wait()
```

### 5d — Overlay `/wake-setup` command

- [ ] **Step 5.7: Add `on_poll_wake_word` slot and `/wake-setup` command to `overlay.py`**

In `src/spaiOS/ui/overlay.py`, inside `_on_prompt_submitted`, add this block after the `/remember` handler (around line 163) and before the final `self._input_row.set_enabled(False)`:

```python
        if prompt.strip().lower() == "/wake-setup":
            self._input_row.clear()
            self._input_row.set_enabled(True)
            self._input_row.focus()
            self._reset_idle_timer()
            self._show_wake_setup()
            return
```

Add these two methods to the `Overlay` class:

```python
    def _show_wake_setup(self) -> None:
        from spaiOS.ui.wake_setup import WakeSetupDialog
        dlg = WakeSetupDialog(self)
        dlg.setup_complete.connect(self._on_wake_setup_complete)
        dlg.exec()

    def _on_wake_setup_complete(self, profile) -> None:
        count = len(profile.phrases)
        self._response_view.show_response(
            f"Wake word updated — {count} trigger phrase(s) active.\n"
            "Restart spaiOS for the new phrase to take effect."
        )

    @pyqtSlot()
    def on_poll_wake_word(self) -> None:
        if not self.isVisible():
            super().show()
            self._start_fade_in()
            self.raise_()
            self.activateWindow()
        self._idle_timer.stop()
        self._sphere.set_state("idle")
        self._response_view.show_response(
            "Custom wake phrase detected — type your command or press "
            "Super+Shift+Space to speak."
        )
        self._input_row.set_enabled(True)
        self._input_row.focus()
        self._reset_idle_timer()
```

### 5e — `main.py` signal wiring

- [ ] **Step 5.8: Connect `poll_wake` signal in `main.py`**

In `src/spaiOS/main.py`, after the existing `wake_listener.audio_ready.connect(...)` line, add:

```python
    wake_listener.poll_wake.connect(overlay.on_poll_wake_word)
```

### 5f — Run full test suite

- [ ] **Step 5.9: Run all tests**

```bash
uv run pytest --tb=short -q
```
Expected: all existing tests pass + the new voice fuzzy-match tests pass. Count should be prior total + 5.

- [ ] **Step 5.10: Lint everything changed**

```bash
uv run black src/spaiOS/core/voice.py src/spaiOS/ui/overlay.py src/spaiOS/main.py --check
uv run flake8 src/spaiOS/core/voice.py src/spaiOS/ui/overlay.py src/spaiOS/main.py --max-line-length=100
```
Reformat with `uv run black <file>` for any failures, then re-run flake8.

- [ ] **Step 5.11: Commit**

```bash
git add src/spaiOS/core/voice.py src/spaiOS/ui/overlay.py src/spaiOS/main.py tests/test_voice.py
git commit -m "Add multi-phrase wake detection: WhisperPollThread + /wake-setup command"
```

---

## Self-Review Checklist

After all tasks are complete, verify these against the spec:

- [ ] User can type `/wake-setup` → `WakeSetupDialog` opens
- [ ] Dialog presents two choices: "Hi Spai" preset and custom phrase
- [ ] Custom phrase input is shown only when "Choose my own phrase" is selected
- [ ] Dialog records 5 positive + 3 negative clips with countdown
- [ ] Calibration runs Whisper on all 5 clips, stores most common transcription as `whisper_target`
- [ ] WAV files saved under `~/.local/share/spaiOS/wake-samples/<slug>/`
- [ ] Profile saved to `~/.local/share/spaiOS/wake_profile.json`
- [ ] "Hi Spai" gets mode `oww_whisper` (OWW catches it, Whisper confirms)
- [ ] Arbitrary phrases get mode `whisper_poll` (background Whisper polling)
- [ ] `WhisperPollThread` reads from audio queue only when NOT in OWW utterance
- [ ] `poll_wake` signal shows overlay via `on_poll_wake_word` slot
- [ ] All new tests pass, no regressions

---

## Notes for Implementer

**"Hi Spai" vs OWW**: The `hey_jarvis_v0.1` OWW model fires on phonetically similar phrases. "Hi Spai" (starts like "Hey J-") activates it reliably enough. The mode `oww_whisper` means OWW provides the detection; the `whisper_target` is stored but not actively used in detection (it's for future verifier training). The user's accent is captured in the WAV files.

**Completely custom phrases (e.g., "Cutto")**: OWW won't fire on these. `WhisperPollThread` handles them via background Whisper inference on a rolling 3-second window. Latency is 3–4 seconds. This is acceptable for a wake phrase.

**CPU budget**: `WhisperPollThread` runs `faster-whisper tiny.int8` on CPU every 3 seconds (~0.5–1s per inference on i7-7700HQ). This consumes ~25–30% of one core continuously. Only active if the user has configured at least one `whisper_poll` phrase.

**Restart required for new phrase**: The `WakeWordListener.run()` loads the profile once at startup. After setup, the user must restart spaiOS (or we later add live-reload). The overlay message makes this clear.

**Verifier training (future)**: WAV files are saved for all phrases. A future task can call `openwakeword.train_custom_verifier(positive_dir, negative_dir, ...)` to produce a `.joblib` personal verifier for OWW-compatible phrases, improving false-positive rejection. Requires adding `scikit-learn` to `pyproject.toml`.
