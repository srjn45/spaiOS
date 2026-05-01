import urllib.request
import wave
from pathlib import Path

import noisereduce as nr
import numpy as np
import onnxruntime as ort
import sounddevice as sd
from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

_MODEL_SIZE = "tiny"
_SAMPLE_RATE = 16000
_CHANNELS = 1
_OWW_CHUNK = 1280  # samples openWakeWord expects per frame (~80ms)

_WAKE_MODEL_NAME = "hey_jarvis_v0.1"
_WAKE_THRESHOLD = 0.5

_VAD_CHUNK = 512  # samples Silero VAD processes per call (32ms @ 16kHz)
_VAD_SILENCE_CHUNKS = 48  # ~1.5s silence before utterance ends (48 * 512 / 16000)
_VAD_SPEECH_THRESHOLD = 0.3  # lower than default 0.5 to handle noisy mic environments
_UTTERANCE_MAX_S = 12.0  # hard-cap safety net
_NOISE_PROFILE_S = 1.5  # seconds of ambient audio captured at startup

_SILERO_ONNX_URL = (
    "https://github.com/snakers4/silero-vad/raw/master"
    "/src/silero_vad/data/silero_vad.onnx"
)
_SILERO_ONNX_PATH = (
    Path.home() / ".local" / "share" / "spaiOS" / "models" / "silero_vad.onnx"
)

_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def vosk_model_path() -> Path:
    # kept so existing tests that import this symbol don't break
    return (
        Path.home()
        / ".local"
        / "share"
        / "spaiOS"
        / "models"
        / "vosk-model-small-en-us-0.15"
    )


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


class SileroVAD:
    """Wraps the Silero VAD ONNX model for per-chunk speech detection."""

    def __init__(self) -> None:
        if not _SILERO_ONNX_PATH.exists():
            _SILERO_ONNX_PATH.parent.mkdir(parents=True, exist_ok=True)
            print("[spaiOS] Downloading Silero VAD ONNX model…")
            urllib.request.urlretrieve(_SILERO_ONNX_URL, _SILERO_ONNX_PATH)
            print("[spaiOS] Silero VAD model downloaded")
        self._session = ort.InferenceSession(
            str(_SILERO_ONNX_PATH),
            providers=["CPUExecutionProvider"],
        )
        self.reset()

    def reset(self) -> None:
        # v5 model uses a single combined state tensor [2, batch, 128]
        self._state = np.zeros((2, 1, 128), dtype=np.float32)

    def predict(self, chunk: np.ndarray) -> float:
        """Feed a _VAD_CHUNK-sample float32 array; return speech probability 0–1."""
        audio = chunk.reshape(1, -1).astype(np.float32)
        sr = np.array(_SAMPLE_RATE, dtype=np.int64)
        outputs = self._session.run(
            ["output", "stateN"],
            {"input": audio, "state": self._state, "sr": sr},
        )
        speech_prob, self._state = outputs
        return float(speech_prob[0][0])


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

    def __init__(
        self, audio: np.ndarray, noise_profile: np.ndarray | None = None
    ) -> None:
        super().__init__()
        self._audio = audio
        self._noise_profile = noise_profile

    def run(self) -> None:
        try:
            audio = self._audio
            if self._noise_profile is not None:
                audio = nr.reduce_noise(
                    y=audio, sr=_SAMPLE_RATE, y_noise=self._noise_profile
                )
            model = _get_whisper_model()
            segments, _ = model.transcribe(audio, language="en")
            text = " ".join(seg.text.strip() for seg in segments).strip()
            self.result.emit(text)
        except Exception as exc:
            self.error.emit(f"Transcription failed: {exc}")


def save_wav(audio: np.ndarray, path: Path) -> None:
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


class WakeWordListener(QThread):
    wake = pyqtSignal()
    # Emits (audio: np.ndarray, noise_profile: np.ndarray) once end-of-speech is detected.
    audio_ready = pyqtSignal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def run(self) -> None:
        from openwakeword.model import Model  # lazy — large import, not needed in tests
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
            # ── Noise profile calibration ──────────────────────────────────────
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
            print(
                "[spaiOS] Noise profile ready. Wake word listener active — say 'hey Jarvis'"
            )

            # ── Main loop ──────────────────────────────────────────────────────
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

                if in_utterance:
                    utterance_frames.append(raw)
                    float_chunk = pcm16.astype(np.float32) / 32768.0
                    utterance_n += len(pcm16)
                    vad_buffer.extend(float_chunk.tolist())

                    # Run VAD on 512-sample windows
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

                    end_by_vad = (
                        speech_detected and silence_chunks >= _VAD_SILENCE_CHUNKS
                    )
                    end_by_timeout = utterance_n >= _utterance_max

                    if end_by_vad or end_by_timeout:
                        reason = "VAD silence" if end_by_vad else "12s timeout"
                        audio = (
                            np.frombuffer(
                                b"".join(utterance_frames), dtype="int16"
                            ).astype(np.float32)
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

    def stop(self) -> None:
        self._running = False
        self.wait()
