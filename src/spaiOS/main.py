import sys

from PyQt6.QtCore import QMetaObject, Qt
from PyQt6.QtWidgets import QApplication

from spaiOS.core.hotkey import HotkeyListener
from spaiOS.core.voice import WakeWordListener
from spaiOS.ui.overlay import Overlay


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = Overlay()

    # pynput fires on daemon threads; route all calls onto the Qt main thread.
    def _toggle_safe() -> None:
        QMetaObject.invokeMethod(overlay, "toggle", Qt.ConnectionType.QueuedConnection)

    def _voice_safe() -> None:
        QMetaObject.invokeMethod(
            overlay, "toggle_voice", Qt.ConnectionType.QueuedConnection
        )

    hotkey = HotkeyListener(_toggle_safe, _voice_safe)
    hotkey.start()

    wake_listener = WakeWordListener()
    wake_listener.wake.connect(overlay.on_wake_word)
    wake_listener.audio_ready.connect(overlay.on_wake_audio_ready)
    wake_listener.poll_wake.connect(overlay.on_poll_wake_word)
    wake_listener.start()
    overlay.set_wake_listener_active(True)

    print(
        "[spaiOS] Running — Super+Space to show overlay, Super+Shift+Space for voice.\n"
        "[spaiOS] Wake word listener active — say 'hey spaiOS' to start."
    )
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
