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
