"""Stubs for audio hardware libraries not available in CI/headless test environments."""
import sys
from unittest.mock import MagicMock

# sounddevice requires PortAudio at import time; stub it before any module imports it.
if "sounddevice" not in sys.modules:
    sys.modules["sounddevice"] = MagicMock()

# vosk requires native shared libraries; stub it too.
if "vosk" not in sys.modules:
    sys.modules["vosk"] = MagicMock()
