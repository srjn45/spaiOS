"""Code-focused agent: read/write files with diff preview, run commands, open in editor."""

import difflib
import os
import subprocess
from pathlib import Path

_BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs.",
    "dd if=",
    "dd of=/dev/",
    "wipefs",
    ":(){ :|:& };:",
    "chmod -r 777 /",
    "shred /dev/",
    "> /dev/sd",
]

_DEFAULT_EDITOR = "nano"
_DEFAULT_TIMEOUT = 30.0


class WriteConfirmationRequired(Exception):
    """Raised by write_file to show a diff and request user confirmation."""

    def __init__(self, path: str, new_content: str, diff: str):
        self.path = path
        self.new_content = new_content
        self.diff = diff
        super().__init__(f"Confirmation required to write: {path}")


class CommandBlocked(Exception):
    """Raised when a terminal command matches a dangerous pattern."""


class CodeAgent:
    def read_file(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return p.read_text(encoding="utf-8", errors="replace")

    def write_file(self, path: str, content: str) -> None:
        """Always raises WriteConfirmationRequired with a unified diff — never writes directly."""
        p = Path(path)
        old_lines = (
            p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            if p.exists()
            else []
        )
        new_lines = content.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{p.name}" if p.exists() else "/dev/null",
                tofile=f"b/{p.name}",
            )
        )
        diff_text = (
            "".join(diff_lines)
            if diff_lines
            else f"+++ b/{p.name}\n" + "".join(f"+{line}" for line in new_lines)
        )

        raise WriteConfirmationRequired(path=path, new_content=content, diff=diff_text)

    def confirm_write(self, path: str, content: str) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Written: {path}"

    def run_terminal_command(self, cmd: str, timeout: float = _DEFAULT_TIMEOUT) -> str:
        lowered = cmd.lower()
        for pattern in _BLOCKED_PATTERNS:
            if pattern in lowered:
                raise CommandBlocked(f"Command blocked for safety: {cmd}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = (result.stdout + result.stderr).strip()
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"

    def open_in_editor(self, path: str) -> str:
        editor = os.environ.get("EDITOR", _DEFAULT_EDITOR)
        subprocess.Popen([editor, path])
        return f"Opened {path} in {editor}"
