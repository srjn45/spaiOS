import sys

from PyQt6.QtCore import QMetaObject, Qt
from PyQt6.QtWidgets import QApplication

from spaiOS.core.hotkey import HotkeyListener
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

    print(
        "[spaiOS] Running — Super+Space to show overlay, Super+Shift+Space for voice."
    )
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
