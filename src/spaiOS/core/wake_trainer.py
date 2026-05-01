from collections import Counter
from pathlib import Path

import numpy as np

from spaiOS.core.voice import _get_whisper_model

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
