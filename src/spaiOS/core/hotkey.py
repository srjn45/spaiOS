import threading
from typing import Callable

from pynput import keyboard


class HotkeyListener:
    """Listens for global hotkeys in a background daemon thread.

    - Super+Space       → toggle_fn  (show/hide overlay)
    - Super+Shift+Space → voice_fn   (start/stop voice recording)
    """

    def __init__(
        self,
        toggle_fn: Callable[[], None],
        voice_fn: Callable[[], None] | None = None,
    ) -> None:
        self._toggle_fn = toggle_fn
        self._voice_fn = voice_fn
        self._thread: threading.Thread | None = None
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        hotkeys: dict[str, Callable[[], None]] = {
            "<cmd>+<space>": self._on_hotkey,
        }
        if self._voice_fn is not None:
            hotkeys["<cmd>+<shift>+<space>"] = self._on_voice_hotkey
        self._listener = keyboard.GlobalHotKeys(hotkeys)
        self._thread = threading.Thread(target=self._listener.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()

    def _on_hotkey(self) -> None:
        self._toggle_fn()

    def _on_voice_hotkey(self) -> None:
        if self._voice_fn is not None:
            self._voice_fn()
