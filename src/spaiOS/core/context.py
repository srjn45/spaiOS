import subprocess
from typing import Optional

try:
    import pyatspi

    _ATSPI_AVAILABLE = True
except ImportError:
    _ATSPI_AVAILABLE = False


def get_window_info() -> dict:
    """Return active window metadata via xdotool."""
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        title = result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        title = ""

    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowpid"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        pid = result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pid = ""

    app_name = _app_name_from_pid(pid)
    return {"app_name": app_name, "window_title": title, "pid": pid}


def _app_name_from_pid(pid: str) -> str:
    if not pid:
        return ""
    try:
        result = subprocess.run(
            ["ps", "-p", pid, "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _walk_atspi_node(node, texts: list, max_chars: int) -> None:
    """Recursively collect visible text from an AT-SPI accessibility tree node."""
    total = sum(len(t) for t in texts)
    if total >= max_chars:
        return

    try:
        text_iface: Optional[object] = node.queryText()
        content = text_iface.getText(0, text_iface.characterCount).strip()
        if content:
            texts.append(content)
    except Exception:
        pass

    try:
        for i in range(node.childCount):
            child = node.getChildAtIndex(i)
            if child is not None:
                _walk_atspi_node(child, texts, max_chars)
                if sum(len(t) for t in texts) >= max_chars:
                    break
    except Exception:
        pass


def get_atspi_text(max_chars: int = 2000) -> list[str]:
    """Return a list of text strings from the focused window's accessibility tree."""
    if not _ATSPI_AVAILABLE:
        return []

    texts: list[str] = []
    try:
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            if app is None:
                continue
            try:
                for window in app:
                    if window is None:
                        continue
                    state_set = window.getState()
                    if state_set.contains(pyatspi.STATE_ACTIVE):
                        _walk_atspi_node(window, texts, max_chars)
                        return texts
            except Exception:
                continue
    except Exception:
        pass

    return texts


def capture() -> dict:
    """Return a snapshot of the current focused window context."""
    info = get_window_info()
    text_chunks = get_atspi_text()
    visible_text = "\n".join(text_chunks)[:2000]
    return {
        "app_name": info["app_name"],
        "window_title": info["window_title"],
        "visible_text": visible_text,
    }
