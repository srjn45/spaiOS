import numpy as np
import pytest

from spaiOS.core.voice import SilenceDetector, is_wake_phrase, vosk_model_path

_SR = 16000  # sample rate used throughout


# ── is_wake_phrase ─────────────────────────────────────────────────────────────

def test_exact_wake_phrase_matches():
    assert is_wake_phrase("hey spaios") is True


def test_wake_phrase_case_insensitive():
    assert is_wake_phrase("Hey SpaiOS") is True
    assert is_wake_phrase("HEY SPAIOS") is True


def test_unrelated_phrase_does_not_match():
    assert is_wake_phrase("hello there") is False


def test_partial_wake_phrase_does_not_match():
    assert is_wake_phrase("spaios") is False


def test_wake_phrase_embedded_at_start():
    assert is_wake_phrase("hey spaios what time is it") is True


def test_vosk_variant_spa_ios_matches():
    assert is_wake_phrase("hey spa ios") is True


def test_vosk_variant_space_ios_matches():
    assert is_wake_phrase("hey space ios") is True


def test_vosk_variant_spy_os_does_not_match():
    # too different — don't accept arbitrary mis-transcriptions
    assert is_wake_phrase("hey spy os") is False


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
