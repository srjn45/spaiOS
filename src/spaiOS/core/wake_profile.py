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
