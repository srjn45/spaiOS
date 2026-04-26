"""Unit tests for FileAgent — all operations run against a temp sandbox."""

import pytest
from pathlib import Path

from spaiOS.agents.file_agent import (
    FileAgent,
    SandboxViolation,
    SystemPathBlocked,
    DeleteConfirmationRequired,
)


@pytest.fixture
def agent(tmp_path):
    return FileAgent(sandbox_path=str(tmp_path))


@pytest.fixture
def populated(agent, tmp_path):
    """Sandbox with a few files and a subfolder."""
    (tmp_path / "notes.txt").write_text("hello world")
    (tmp_path / "data.csv").write_text("a,b\n1,2")
    (tmp_path / "image.jpg").write_bytes(b"\xff\xd8\xff fake")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "nested.txt").write_text("nested content")
    return agent


# --- list_directory ---


def test_list_directory_root(populated, tmp_path):
    entries = populated.list_directory()
    names = {e.name for e in entries}
    assert "notes.txt" in names
    assert "sub" in names


def test_list_directory_subdir(populated):
    entries = populated.list_directory("sub")
    assert len(entries) == 1
    assert entries[0].name == "nested.txt"
    assert not entries[0].is_dir


def test_list_directory_nonexistent(agent):
    with pytest.raises(NotADirectoryError):
        agent.list_directory("ghost")


# --- create_folder ---


def test_create_folder(agent):
    result = agent.create_folder("new/deep/dir")
    assert result == "new/deep/dir"
    assert (Path(agent.sandbox) / "new" / "deep" / "dir").is_dir()


def test_create_folder_existing_is_ok(agent):
    agent.create_folder("already")
    agent.create_folder("already")  # idempotent


# --- move_file ---


def test_move_file_to_subdir(populated):
    populated.create_folder("archive")
    result = populated.move_file("notes.txt", "archive")
    assert result == "archive/notes.txt"
    assert not (Path(populated.sandbox) / "notes.txt").exists()
    assert (Path(populated.sandbox) / "archive" / "notes.txt").exists()


def test_move_file_explicit_destination(populated):
    result = populated.move_file("notes.txt", "notes_moved.txt")
    assert result == "notes_moved.txt"


def test_move_file_not_found(agent):
    with pytest.raises(FileNotFoundError):
        agent.move_file("ghost.txt", "somewhere.txt")


# --- rename_file ---


def test_rename_file(populated):
    result = populated.rename_file("notes.txt", "notes_renamed.txt")
    assert result == "notes_renamed.txt"
    assert (Path(populated.sandbox) / "notes_renamed.txt").exists()
    assert not (Path(populated.sandbox) / "notes.txt").exists()


def test_rename_file_rejects_path_in_name(populated):
    with pytest.raises(ValueError):
        populated.rename_file("notes.txt", "subdir/sneaky.txt")


def test_rename_file_not_found(agent):
    with pytest.raises(FileNotFoundError):
        agent.rename_file("ghost.txt", "new.txt")


# --- delete_file ---


def test_delete_file_requires_confirmation(populated):
    with pytest.raises(DeleteConfirmationRequired) as exc:
        populated.delete_file("notes.txt")
    assert "notes.txt" in str(exc.value)


def test_delete_file_confirmed(populated):
    result = populated.delete_file("notes.txt", confirmed=True)
    assert result == "notes.txt"
    assert not (Path(populated.sandbox) / "notes.txt").exists()


def test_delete_file_not_found(agent):
    with pytest.raises(FileNotFoundError):
        agent.delete_file("ghost.txt", confirmed=True)


def test_delete_empty_dir(agent, tmp_path):
    (tmp_path / "emptydir").mkdir()
    agent.delete_file("emptydir", confirmed=True)
    assert not (tmp_path / "emptydir").exists()


# --- read_file_summary ---


def test_read_file_summary_text(populated):
    summary = populated.read_file_summary("notes.txt")
    assert "hello world" in summary


def test_read_file_summary_truncates(agent, tmp_path):
    (tmp_path / "long.txt").write_text("x" * 1000)
    summary = agent.read_file_summary("long.txt", max_chars=10)
    assert summary == "xxxxxxxxxx…"


def test_read_file_summary_binary(populated):
    summary = populated.read_file_summary("image.jpg")
    assert summary.startswith("[binary]")


def test_read_file_summary_not_found(agent):
    with pytest.raises(FileNotFoundError):
        agent.read_file_summary("ghost.txt")


def test_read_file_summary_directory(populated):
    with pytest.raises(IsADirectoryError):
        populated.read_file_summary("sub")


# --- sandbox security ---


def test_path_traversal_blocked(agent):
    with pytest.raises(SandboxViolation):
        agent._resolve("../../etc/passwd")


def test_absolute_path_treated_as_relative(agent, tmp_path):
    # "/notes.txt" should resolve inside sandbox, not filesystem root
    (tmp_path / "notes.txt").write_text("hi")
    path = agent._resolve("/notes.txt")
    assert path == tmp_path / "notes.txt"


def test_system_path_blocked(agent):
    # Override sandbox to allow resolving /etc paths for this test
    with pytest.raises(SystemPathBlocked):
        agent._resolve("/etc/passwd")


def test_sandbox_violation_on_symlink_escape(agent, tmp_path, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    link = tmp_path / "escape_link"
    link.symlink_to(outside)
    with pytest.raises(SandboxViolation):
        agent._resolve("escape_link/anything")
