import threading
from typing import Callable

from pynput import keyboard


class HotkeyListener:
    """Listens for Super+Space in a background daemon thread and calls toggle_fn."""

    def __init__(self, toggle_fn: Callable[[], None]) -> None:
        self._toggle_fn = toggle_fn
        self._thread: threading.Thread | None = None
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        self._listener = keyboard.GlobalHotKeys({"<cmd>+<space>": self._on_hotkey})
        self._thread = threading.Thread(target=self._listener.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()

    def _on_hotkey(self) -> None:
        # pynput fires on a background thread; Qt calls must go through signals.
        # toggle_fn is expected to be a thread-safe Qt slot invoked via QMetaObject.
        self._toggle_fn()
