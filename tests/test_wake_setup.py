import pytest


# ── assign_wake_mode ──────────────────────────────────────────────────────────

def test_hi_spai_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("hi spai") == "oww_whisper"


def test_hey_jarvis_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("hey jarvis") == "oww_whisper"


def test_alexa_is_oww_whisper():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("alexa") == "oww_whisper"


def test_custom_phrase_is_whisper_poll():
    from spaiOS.ui.wake_setup import assign_wake_mode
    assert assign_wake_mode("cutto") == "whisper_poll"
    assert assign_wake_mode("banana boat") == "whisper_poll"
    assert assign_wake_mode("start session") == "whisper_poll"


# ── dialog smoke test ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def qapp():
    from PyQt6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_wake_setup_dialog_constructs(qapp):
    from unittest.mock import patch
    with patch("spaiOS.ui.wake_setup.load_profile"), \
         patch("spaiOS.ui.wake_setup.save_profile"):
        from spaiOS.ui.wake_setup import WakeSetupDialog
        dlg = WakeSetupDialog()
        assert dlg.windowTitle() == "Wake Word Setup"
        dlg.destroy()
