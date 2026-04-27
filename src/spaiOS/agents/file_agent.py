"""File management agent — all operations sandboxed to a configurable base path."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

SYSTEM_PATH_BLOCKLIST = (
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    "/lib",
    "/lib64",
    "/proc",
    "/sys",
    "/dev",
    "/run",
    "/snap",
)

DEFAULT_SANDBOX = os.path.expanduser("~/spaiOS-sandbox")


class SandboxViolation(Exception):
    """Raised when a path resolves outside the sandbox."""


class SystemPathBlocked(Exception):
    """Raised when a path targets a protected system directory."""


class DeleteConfirmationRequired(Exception):
    """Raised by delete_file when confirmed=True was not passed."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Confirmation required to delete: {path}")


@dataclass
class FileEntry:
    name: str
    path: str
    is_dir: bool
    size_bytes: int
    extension: str


class FileAgent:
    def __init__(self, sandbox_path: str = DEFAULT_SANDBOX):
        self.sandbox = Path(sandbox_path).expanduser().resolve()
        self.sandbox.mkdir(parents=True, exist_ok=True)

    def _resolve(self, user_path: str) -> Path:
        """Resolve user_path relative to sandbox and validate it stays inside."""
        # Block explicit system paths before any sandbox-relative rewriting
        if user_path.startswith("/"):
            for blocked in SYSTEM_PATH_BLOCKLIST:
                if user_path == blocked or user_path.startswith(blocked + "/"):
                    raise SystemPathBlocked(
                        f"Path targets a protected system directory: {user_path}"
                    )

        # Treat absolute paths as relative to sandbox root
        cleaned = user_path.lstrip("/")
        candidate = (self.sandbox / cleaned).resolve()

        for blocked in SYSTEM_PATH_BLOCKLIST:
            if str(candidate).startswith(blocked + "/") or str(candidate) == blocked:
                raise SystemPathBlocked(
                    f"Path targets a protected system directory: {candidate}"
                )

        try:
            candidate.relative_to(self.sandbox)
        except ValueError:
            raise SandboxViolation(
                f"Path '{user_path}' resolves outside sandbox: {candidate}"
            )

        return candidate

    def list_directory(self, subpath: str = "") -> list[FileEntry]:
        """Return entries in a sandbox directory."""
        target = self._resolve(subpath)
        if not target.is_dir():
            raise NotADirectoryError(f"Not a directory: {subpath}")

        entries = []
        for entry in sorted(target.iterdir()):
            stat = entry.stat()
            entries.append(
                FileEntry(
                    name=entry.name,
                    path=str(entry.relative_to(self.sandbox)),
                    is_dir=entry.is_dir(),
                    size_bytes=stat.st_size if not entry.is_dir() else 0,
                    extension=entry.suffix.lower() if not entry.is_dir() else "",
                )
            )
        return entries

    def create_folder(self, subpath: str) -> str:
        """Create a folder inside the sandbox. Returns the created path."""
        target = self._resolve(subpath)
        target.mkdir(parents=True, exist_ok=True)
        return str(target.relative_to(self.sandbox))

    def move_file(self, src: str, dst: str) -> str:
        """Move src to dst (both sandbox-relative). Returns new relative path."""
        src_path = self._resolve(src)
        dst_path = self._resolve(dst)

        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src}")

        if dst_path.is_dir():
            dst_path = dst_path / src_path.name

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        return str(dst_path.relative_to(self.sandbox))

    def rename_file(self, src: str, new_name: str) -> str:
        """Rename a file within its current directory. Returns new relative path."""
        src_path = self._resolve(src)
        if not src_path.exists():
            raise FileNotFoundError(f"Not found: {src}")

        if "/" in new_name or "\\" in new_name:
            raise ValueError("new_name must be a bare filename, not a path")

        dst_path = src_path.parent / new_name
        # dst_path is in the same dir as src — still inside sandbox, no extra check needed
        src_path.rename(dst_path)
        return str(dst_path.relative_to(self.sandbox))

    def delete_file(self, subpath: str, confirmed: bool = False) -> str:
        """
        Delete a file or empty directory.

        Raises DeleteConfirmationRequired unless confirmed=True is explicitly passed.
        Returns the path that was deleted.
        """
        target = self._resolve(subpath)
        if not target.exists():
            raise FileNotFoundError(f"Not found: {subpath}")

        if not confirmed:
            raise DeleteConfirmationRequired(str(target.relative_to(self.sandbox)))

        if target.is_dir():
            target.rmdir()  # only removes empty dirs — intentional safety
        else:
            target.unlink()

        return str(target.relative_to(self.sandbox))

    def read_file_summary(self, subpath: str, max_chars: int = 500) -> str:
        """
        Return a short text preview of a file.

        Binary files get a hex dump of the first 32 bytes instead.
        """
        target = self._resolve(subpath)
        if not target.exists():
            raise FileNotFoundError(f"Not found: {subpath}")
        if target.is_dir():
            raise IsADirectoryError(f"Cannot summarize a directory: {subpath}")

        try:
            text = target.read_text(encoding="utf-8", errors="strict")
            return text[:max_chars] + ("…" if len(text) > max_chars else "")
        except UnicodeDecodeError:
            raw = target.read_bytes()[:32]
            return f"[binary] {raw.hex(' ')}"
