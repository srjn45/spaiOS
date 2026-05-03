from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field

_SOCK_PATH = os.path.expanduser("~/.local/share/spaish/spaid.sock")
_SESSION_ID = "overlay-default"

log = logging.getLogger(__name__)


@dataclass
class ResponseEvent:
    type: str  # "text" | "tool_call" | "done" | "error"
    content: str = ""
    tool: str = ""
    params: dict = field(default_factory=dict)


class SpaidClient:
    def __init__(self, sock_path: str = _SOCK_PATH) -> None:
        self._sock_path = sock_path

    def is_available(self) -> bool:
        return os.path.exists(self._sock_path)

    def get_active_window(self) -> dict:
        try:
            win_id = subprocess.check_output(
                ["xdotool", "getactivewindow"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            title = subprocess.check_output(
                ["xdotool", "getwindowname", win_id],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            pid_raw = subprocess.check_output(
                ["xdotool", "getwindowpid", win_id],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return {
                "title": title,
                "win_id": hex(int(win_id)),
                "pid": int(pid_raw) if pid_raw else 0,
            }
        except Exception as exc:
            log.debug("get_active_window failed: %s", exc)
            return {}

    def query(self, text: str, active_window: dict) -> Iterator[ResponseEvent]:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self._sock_path)

        req = {
            "type": "overlay_query",
            "session_id": _SESSION_ID,
            "overlay": {
                "query": text,
                "session_id": _SESSION_ID,
                "active_window": active_window if active_window else None,
            },
        }
        payload = (json.dumps(req) + "\n").encode()
        sock.sendall(payload)

        buf = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    event = ResponseEvent(
                        type=data.get("type", ""),
                        content=data.get("content", ""),
                        tool=data.get("tool", ""),
                        params=data.get("params") or {},
                    )
                    yield event
                    if event.type in ("done", "error"):
                        return
        finally:
            sock.close()
