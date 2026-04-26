from unittest.mock import MagicMock

from spaiOS.core.orchestrator import _build_system_prompt, _emit_ollama_error, is_clarifying_question


# ── is_clarifying_question ─────────────────────────────────────────────────────

def test_question_mark_at_end():
    assert is_clarifying_question("What do you mean?") is True


def test_question_mark_mid_sentence_not_enough():
    assert is_clarifying_question("It works! But are you sure? Yes.") is False


def test_statement_returns_false():
    assert is_clarifying_question("Here is the answer.") is False


def test_clarifying_prefix_could_you_clarify():
    assert is_clarifying_question("Could you clarify what file you mean?") is True


def test_clarifying_prefix_can_you_tell_me():
    assert is_clarifying_question("Can you tell me which folder to use?") is True


def test_clarifying_prefix_which_one():
    assert is_clarifying_question("Which one do you want me to edit?") is True


def test_empty_string_returns_false():
    assert is_clarifying_question("") is False


# ── _build_system_prompt ───────────────────────────────────────────────────────

def test_build_prompt_includes_all_fields():
    ctx = {
        "app_name": "code",
        "window_title": "main.py — VS Code",
        "visible_text": "def foo():\n    pass",
    }
    result = _build_system_prompt(ctx)
    assert "code" in result
    assert "main.py" in result
    assert "def foo()" in result


def test_build_prompt_empty_context_returns_empty():
    assert _build_system_prompt({}) == ""


def test_build_prompt_partial_context():
    ctx = {"app_name": "firefox"}
    result = _build_system_prompt(ctx)
    assert "firefox" in result
    assert "Window title" not in result


# ── _emit_ollama_error ─────────────────────────────────────────────────────────

def _capture_emit(exc: Exception) -> str:
    signal = MagicMock()
    _emit_ollama_error(exc, signal)
    return signal.emit.call_args[0][0]


def test_connection_refused_message():
    msg = _capture_emit(ConnectionRefusedError("connection refused"))
    assert "ollama serve" in msg


def test_model_not_found_message():
    msg = _capture_emit(Exception("model 'llama3.2:3b' not found"))
    assert "ollama pull" in msg


def test_timeout_message():
    msg = _capture_emit(Exception("request timed out"))
    assert "Try again" in msg or "try again" in msg


def test_generic_error_passthrough():
    msg = _capture_emit(Exception("something unexpected"))
    assert "something unexpected" in msg
