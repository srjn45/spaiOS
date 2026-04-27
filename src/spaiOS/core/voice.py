from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

_MODEL_SIZE = "tiny"
_SAMPLE_RATE = 16000
_CHANNELS = 1
_OWW_CHUNK = 1280  # samples openWakeWord expects per frame (~80ms)

_WAKE_MODEL_NAME = "hey_jarvis_v0.1"
_WAKE_THRESHOLD = 0.5

_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def vosk_model_path() -> Path:
    # kept so existing tests that import this symbol don't break
    return Path.home() / ".local" / "share" / "spaiOS" / "models" / "vosk-model-small-en-us-0.15"


class SilenceDetector:
    def __init__(
        self,
        threshold_seconds: float = 1.5,
        sample_rate: int = _SAMPLE_RATE,
        energy_floor: float = 0.15,
    ) -> None:
        self._threshold_samples = int(threshold_seconds * sample_rate)
        self._energy_floor = energy_floor
        self._silent_samples = 0

    def feed(self, frame: np.ndarray) -> bool:
        rms = float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))
        if rms < self._energy_floor:
            self._silent_samples += frame.shape[0]
        else:
            self._silent_samples = 0
        return self._silent_samples >= self._threshold_samples

    def reset(self) -> None:
        self._silent_samples = 0


class VoiceRecorder:
    def __init__(self) -> None:
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []

    def start(self) -> None:
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, _frames: int, _time, _status) -> None:
        self._frames.append(indata.copy())

    def stop_and_transcribe(self) -> str:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return ""

        audio = np.concatenate(self._frames, axis=0).flatten().astype(np.float32)
        model = _get_whisper_model()
        segments, _ = model.transcribe(audio, language="en")
        return " ".join(seg.text.strip() for seg in segments).strip()

    @property
    def is_recording(self) -> bool:
        return self._stream is not None and self._stream.active


class VoiceTranscribeThread(QThread):
    result = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, recorder: VoiceRecorder) -> None:
        super().__init__()
        self._recorder = recorder

    def run(self) -> None:
        try:
            text = self._recorder.stop_and_transcribe()
            self.result.emit(text)
        except Exception as exc:
            self.error.emit(f"Transcription failed: {exc}")


class AudioTranscribeThread(QThread):
    """Transcribes a pre-recorded float32 audio array using Whisper."""

    result = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio: np.ndarray) -> None:
        super().__init__()
        self._audio = audio

    def run(self) -> None:
        try:
            model = _get_whisper_model()
            segments, _ = model.transcribe(self._audio, language="en")
            text = " ".join(seg.text.strip() for seg in segments).strip()
            self.result.emit(text)
        except Exception as exc:
            self.error.emit(f"Transcription failed: {exc}")


class WakeWordListener(QThread):
    wake = pyqtSignal()
    # Emits the utterance as a float32 numpy array once end-of-speech is detected.
    audio_ready = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        from openwakeword.model import Model  # lazy — large import, not needed in tests
        import openwakeword

        model_dir = Path(openwakeword.__file__).parent / "resources" / "models"
        model_path = str(model_dir / f"{_WAKE_MODEL_NAME}.onnx")
        oww = Model(wakeword_model_paths=[model_path])
        # Record a fixed window after wake word and transcribe.
        # Energy-based silence detection is unreliable on this hardware (fan noise
        # overlaps with speech RMS), so a timeout is the practical solution.
        _UTTERANCE_MAX = int(6.0 * _SAMPLE_RATE)  # 6-second recording window

        in_utterance = False
        utterance_frames: list[bytes] = []
        utterance_n = 0
        self._running = True

        print("[spaiOS] Wake word listener active — say 'hey Jarvis'")

        with sd.RawInputStream(
            samplerate=_SAMPLE_RATE,
            blocksize=_OWW_CHUNK,
            dtype="int16",
            channels=_CHANNELS,
        ) as stream:
            while self._running:
                data, _ = stream.read(_OWW_CHUNK)
                raw = bytes(data)
                pcm16 = np.frombuffer(raw, dtype="int16")

                if in_utterance:
                    utterance_frames.append(raw)
                    utterance_n += len(pcm16)

                    if utterance_n >= _UTTERANCE_MAX:
                        audio = (
                            np.frombuffer(b"".join(utterance_frames), dtype="int16")
                            .astype(np.float32) / 32768.0
                        )
                        print(f"[spaiOS] 6s window complete — transcribing {len(audio)} samples")
                        self.audio_ready.emit(audio)
                        in_utterance = False
                        utterance_frames = []
                        utterance_n = 0
                        oww.reset()
                else:
                    prediction = oww.predict(pcm16)
                    score = prediction.get(_WAKE_MODEL_NAME, 0.0)
                    if score >= _WAKE_THRESHOLD:
                        print(f"[spaiOS] wake word detected (score={score:.2f})")
                        in_utterance = True
                        utterance_frames = []
                        utterance_n = 0
                        oww.reset()
                        self.wake.emit()

    def stop(self) -> None:
        self._running = False
        self.wait()
