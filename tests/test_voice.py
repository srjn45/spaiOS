import numpy as np
import pytest

from spaiOS.core.voice import SilenceDetector, SileroVAD, vosk_model_path

_SR = 16000  # sample rate used throughout


# ── SilenceDetector ────────────────────────────────────────────────────────────

def _silent_frame(n_samples: int) -> np.ndarray:
    return np.zeros((n_samples, 1), dtype=np.float32)


def _speech_frame(n_samples: int) -> np.ndarray:
    return np.ones((n_samples, 1), dtype=np.float32) * 0.5


def test_silence_not_detected_before_threshold():
    detector = SilenceDetector(threshold_seconds=1.5, sample_rate=_SR)
    # 1.0s of silence — not enough
    result = False
    for _ in range(10):
        result = detector.feed(_silent_frame(1600))  # 10 * 1600 / 16000 = 1.0s
    assert result is False


def test_silence_detected_after_threshold():
    detector = SilenceDetector(threshold_seconds=1.5, sample_rate=_SR)
    # 1.6s of silence — enough
    result = False
    for _ in range(16):
        result = detector.feed(_silent_frame(1600))  # 16 * 1600 / 16000 = 1.6s
    assert result is True


def test_speech_resets_silence_timer():
    detector = SilenceDetector(threshold_seconds=1.5, sample_rate=_SR)
    # 1.0s silence, then speech (resets), then 1.6s silence
    for _ in range(10):
        detector.feed(_silent_frame(1600))
    detector.feed(_speech_frame(1600))  # reset

    result = False
    for _ in range(16):
        result = detector.feed(_silent_frame(1600))
    assert result is True


def test_silence_returns_false_on_mixed_audio():
    detector = SilenceDetector(threshold_seconds=1.5, sample_rate=_SR)
    # alternating silence and speech — never hits threshold
    result = False
    for _ in range(20):
        detector.feed(_silent_frame(800))
        result = detector.feed(_speech_frame(800))
    assert result is False


def test_reset_clears_accumulated_silence():
    detector = SilenceDetector(threshold_seconds=1.5, sample_rate=_SR)
    for _ in range(16):
        detector.feed(_silent_frame(1600))
    detector.reset()
    # after reset, need another full 1.5s of silence
    result = False
    for _ in range(10):
        result = detector.feed(_silent_frame(1600))
    assert result is False


# ── vosk_model_path ───────────────────────────────────────────────────────────

def test_vosk_model_path_under_local_share():
    path = vosk_model_path()
    assert ".local/share/spaiOS" in str(path)


def test_vosk_model_path_contains_model_name():
    path = vosk_model_path()
    assert "vosk-model-small-en-us" in str(path)


# ── noisereduce ───────────────────────────────────────────────────────────────

def test_noisereduce_reduces_rms():
    """noisereduce should substantially lower RMS of a pure-noise signal when
    the noise profile is an identical sample of that same stationary noise."""
    import noisereduce as nr

    rng = np.random.default_rng(42)
    # Stationary white noise (simulates constant fan noise)
    noise = rng.normal(0, 0.05, _SR * 2).astype(np.float32)
    noise_profile = noise[: _SR]  # first half is the "ambient calibration"
    signal = noise[_SR:]           # second half is what we want to clean

    cleaned = nr.reduce_noise(y=signal, sr=_SR, y_noise=noise_profile)

    assert cleaned.shape == signal.shape
    rms_before = float(np.sqrt(np.mean(signal**2)))
    rms_after = float(np.sqrt(np.mean(cleaned**2)))
    assert rms_after < rms_before * 0.8, (
        f"noisereduce should reduce noise RMS by >20%; "
        f"before={rms_before:.4f}, after={rms_after:.4f}"
    )


# ── SileroVAD ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def vad():
    """Load SileroVAD once per module (downloads model if not cached)."""
    return SileroVAD()


def test_silero_vad_silence_scores_low(vad):
    """Pure silence should score below 0.5."""
    vad.reset()
    chunk = np.zeros(512, dtype=np.float32)
    scores = [vad.predict(chunk) for _ in range(5)]
    assert all(s < 0.5 for s in scores), f"Silence scores too high: {scores}"


def test_silero_vad_outputs_valid_probability(vad):
    """predict() must return a float in [0, 1] for any input."""
    vad.reset()
    rng = np.random.default_rng(7)
    for _ in range(8):
        chunk = rng.normal(0, 0.1, 512).astype(np.float32)
        prob = vad.predict(chunk)
        assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"


def test_silero_vad_reset_clears_state(vad):
    """After reset(), state should behave as freshly initialised."""
    t = np.arange(512) / _SR
    tone = (0.4 * np.sin(2 * np.pi * 400 * t)).astype(np.float32)
    # Prime with speech
    for _ in range(10):
        vad.predict(tone)
    vad.reset()
    # After reset, a few silence chunks should score low
    chunk = np.zeros(512, dtype=np.float32)
    scores = [vad.predict(chunk) for _ in range(3)]
    assert all(s < 0.5 for s in scores), f"Scores after reset too high: {scores}"
