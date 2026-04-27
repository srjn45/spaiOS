import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

# tiny model: ~75MB, downloads to ~/.cache on first use
_MODEL_SIZE = "tiny"
_SAMPLE_RATE = 16000
_CHANNELS = 1


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
