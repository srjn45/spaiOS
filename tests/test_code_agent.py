"""Unit tests for CodeAgent — read, write (diff+confirm), run command, open in editor."""

import subprocess as _subprocess

import pytest

from spaiOS.agents.code_agent import (
    CodeAgent,
    CommandBlocked,
    WriteConfirmationRequired,
)


@pytest.fixture
def agent():
    return CodeAgent()


@pytest.fixture
def py_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def greet():\n    return 'hello'\n")
    return f


# --- read_file ---


def test_read_file_returns_content(agent, py_file):
    content = agent.read_file(str(py_file))
    assert "def greet" in content
    assert "return 'hello'" in content


def test_read_file_raises_for_missing_file(agent, tmp_path):
    with pytest.raises(FileNotFoundError):
        agent.read_file(str(tmp_path / "ghost.py"))


# --- write_file (raises WriteConfirmationRequired) ---


def test_write_file_raises_confirmation_required(agent, py_file):
    with pytest.raises(WriteConfirmationRequired):
        agent.write_file(str(py_file), "def greet():\n    return 'hi'\n")


def test_write_file_exception_carries_path_and_content(agent, py_file):
    new_content = "def greet():\n    return 'hi'\n"
    with pytest.raises(WriteConfirmationRequired) as exc_info:
        agent.write_file(str(py_file), new_content)
    exc = exc_info.value
    assert exc.path == str(py_file)
    assert exc.new_content == new_content


def test_write_file_diff_shows_removed_and_added_lines(agent, py_file):
    with pytest.raises(WriteConfirmationRequired) as exc_info:
        agent.write_file(str(py_file), "def greet():\n    return 'hi'\n")
    diff = exc_info.value.diff
    assert "-" in diff
    assert "+" in diff


def test_write_new_file_diff_shows_addition(agent, tmp_path):
    path = str(tmp_path / "new.py")
    with pytest.raises(WriteConfirmationRequired) as exc_info:
        agent.write_file(path, "x = 1\n")
    diff = exc_info.value.diff
    assert "x = 1" in diff


# --- confirm_write ---


def test_confirm_write_creates_new_file(agent, tmp_path):
    path = str(tmp_path / "out.py")
    result = agent.confirm_write(path, "x = 42\n")
    assert "Written" in result or "written" in result.lower()
    from pathlib import Path
    assert Path(path).read_text() == "x = 42\n"


def test_confirm_write_overwrites_existing_file(agent, py_file):
    agent.confirm_write(str(py_file), "x = 1\n")
    assert py_file.read_text() == "x = 1\n"


def test_confirm_write_creates_parent_directories(agent, tmp_path):
    path = str(tmp_path / "a" / "b" / "c.py")
    agent.confirm_write(path, "pass\n")
    from pathlib import Path
    assert Path(path).exists()


# --- run_terminal_command ---


def test_run_terminal_command_returns_stdout(agent):
    result = agent.run_terminal_command("echo hello_world")
    assert "hello_world" in result


def test_run_terminal_command_blocks_rm_rf_slash(agent):
    with pytest.raises(CommandBlocked):
        agent.run_terminal_command("rm -rf /")


def test_run_terminal_command_blocks_mkfs(agent):
    with pytest.raises(CommandBlocked):
        agent.run_terminal_command("mkfs.ext4 /dev/sda")


def test_run_terminal_command_times_out_gracefully(agent):
    result = agent.run_terminal_command("sleep 100", timeout=0.1)
    assert "timed out" in result.lower()


def test_run_terminal_command_no_output_returns_placeholder(agent):
    result = agent.run_terminal_command("true")
    assert isinstance(result, str)
    assert len(result) > 0


# --- open_in_editor ---


def test_open_in_editor_uses_editor_env_var(agent, py_file, monkeypatch):
    launched = []

    class FakePopen:
        def __init__(self, args, **kwargs):
            launched.append(list(args))
            self.pid = 123

    import spaiOS.agents.code_agent as mod

    monkeypatch.setattr(mod.subprocess, "Popen", FakePopen)
    monkeypatch.setenv("EDITOR", "vim")

    result = agent.open_in_editor(str(py_file))

    assert ["vim", str(py_file)] in launched
    assert "vim" in result


def test_open_in_editor_falls_back_when_editor_not_set(agent, py_file, monkeypatch):
    launched = []

    class FakePopen:
        def __init__(self, args, **kwargs):
            launched.append(list(args))
            self.pid = 123

    import spaiOS.agents.code_agent as mod

    monkeypatch.setattr(mod.subprocess, "Popen", FakePopen)
    monkeypatch.delenv("EDITOR", raising=False)

    result = agent.open_in_editor(str(py_file))

    assert len(launched) == 1
    assert str(py_file) in launched[0]
    assert isinstance(result, str)
