from unittest.mock import MagicMock

from spaiOS.core.orchestrator import (
    _build_system_prompt,
    _emit_ollama_error,
    is_clarifying_question,
)

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
    }
    result = _build_system_prompt(ctx)
    assert "code" in result
    assert "main.py" in result
    assert "spaiOS" in result


def test_build_prompt_empty_context_returns_base_prompt():
    result = _build_system_prompt({})
    assert "spaiOS" in result
    assert "sandbox" in result
    assert "Active app" not in result


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
    assert "config.toml" in msg or "model" in msg.lower()


def test_timeout_message():
    msg = _capture_emit(Exception("request timed out"))
    assert "Try again" in msg or "try again" in msg


def test_generic_error_passthrough():
    msg = _capture_emit(Exception("something unexpected"))
    assert "something unexpected" in msg


# ── Orchestrator memory ────────────────────────────────────────────────────────


class TestOrchestratorMemory:
    def test_no_memory_context_when_memory_is_none(self):
        from spaiOS.core.orchestrator import Orchestrator

        orc = Orchestrator(memory=None)
        assert orc._memory_context == ""

    def test_memory_context_loaded_from_store_on_init(self):
        from unittest.mock import MagicMock
        from spaiOS.core.orchestrator import Orchestrator

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = [
            "Date: 2026-04-30\nSummary: Worked on voice pipeline."
        ]
        orc = Orchestrator(memory=mock_memory)
        assert "voice pipeline" in orc._memory_context

    def test_end_session_stores_summary_and_clears_history(self):
        from unittest.mock import MagicMock, patch
        from spaiOS.core.orchestrator import Orchestrator

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = []
        orc = Orchestrator(memory=mock_memory)
        orc._history = [
            {"role": "user", "content": "list files"},
            {"role": "assistant", "content": "You have 2 files."},
        ]

        with patch(
            "spaiOS.core.summarizer.summarize_session",
            return_value="User listed files.",
        ):
            orc.end_session()

        mock_memory.store_session.assert_called_once()
        call_kwargs = mock_memory.store_session.call_args[0]
        assert "User listed files." in call_kwargs
        assert orc._history == []

    def test_end_session_is_noop_when_memory_is_none(self):
        from spaiOS.core.orchestrator import Orchestrator

        orc = Orchestrator(memory=None)
        orc._history = [{"role": "user", "content": "hi"}]
        orc.end_session()
        assert orc._history == []

    def test_system_prompt_includes_memory_context(self):
        from unittest.mock import MagicMock
        from spaiOS.core.orchestrator import Orchestrator, _build_system_prompt

        mock_memory = MagicMock()
        mock_memory.get_recent_sessions.return_value = [
            "Date: 2026-04-30\nSummary: Worked on voice pipeline."
        ]
        orc = Orchestrator(memory=mock_memory)
        prompt = _build_system_prompt({}, orc._memory_context)
        assert "voice pipeline" in prompt
