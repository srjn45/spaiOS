import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

_MODEL_SIZE = "tiny"
_SAMPLE_RATE = 16000
_CHANNELS = 1
_BLOCK_SIZE = 8000  # samples per vosk read (~0.5s)

_VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"
_VOSK_MODEL_URL = f"https://alphacephei.com/vosk/models/{_VOSK_MODEL_NAME}.zip"

# Phrases vosk might produce for "hey spaiOS" — tuned to common mis-transcriptions.
_WAKE_VARIANTS = {"hey spaios", "hey spa ios", "hey space ios", "hey spai os"}


def is_wake_phrase(text: str) -> bool:
    lowered = text.lower().strip()
    return any(lowered == v or lowered.startswith(v + " ") for v in _WAKE_VARIANTS)


def vosk_model_path() -> Path:
    return Path.home() / ".local" / "share" / "spaiOS" / "models" / _VOSK_MODEL_NAME


def ensure_vosk_model() -> Path:
    model_dir = vosk_model_path()
    if model_dir.exists():
        return model_dir

    model_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = model_dir.parent / f"{_VOSK_MODEL_NAME}.zip"

    print(f"[spaiOS] Downloading vosk model (~40MB) → {zip_path}")
    urllib.request.urlretrieve(_VOSK_MODEL_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(model_dir.parent)
    zip_path.unlink()

    return model_dir


class SilenceDetector:
    def __init__(
        self,
        threshold_seconds: float = 1.5,
        sample_rate: int = _SAMPLE_RATE,
        energy_floor: float = 0.01,
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
        self._model: WhisperModel | None = None
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []

    def _load_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
        return self._model

    def start(self) -> None:
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=_SAMPLE_RATE,
            channels=_CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        self._frames.append(indata.copy())

    def stop_and_transcribe(self) -> str:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._frames:
            return ""

        audio = np.concatenate(self._frames, axis=0).flatten().astype(np.float32)
        model = self._load_model()
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


class WakeWordListener(QThread):
    wake = pyqtSignal()
    utterance_end = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        from vosk import KaldiRecognizer, Model  # lazy — native lib not available in tests

        model_dir = ensure_vosk_model()
        model = Model(str(model_dir))
        rec = KaldiRecognizer(model, _SAMPLE_RATE)
        silence = SilenceDetector()
        in_utterance = False
        self._running = True

        with sd.RawInputStream(
            samplerate=_SAMPLE_RATE,
            blocksize=_BLOCK_SIZE,
            dtype="int16",
            channels=_CHANNELS,
        ) as stream:
            while self._running:
                data, _ = stream.read(_BLOCK_SIZE)
                raw = bytes(data)

                if in_utterance:
                    pcm = np.frombuffer(raw, dtype="int16").astype(np.float32) / 32768.0
                    if silence.feed(pcm.reshape(-1, 1)):
                        in_utterance = False
                        silence.reset()
                        self.utterance_end.emit()
                else:
                    if rec.AcceptWaveform(raw):
                        text = json.loads(rec.Result()).get("text", "")
                        if is_wake_phrase(text):
                            in_utterance = True
                            silence.reset()
                            self.wake.emit()

    def stop(self) -> None:
        self._running = False
        self.wait()
