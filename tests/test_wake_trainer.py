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
