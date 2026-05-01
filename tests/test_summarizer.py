from unittest.mock import patch


class TestSummarizeSession:
    def test_returns_empty_string_for_empty_history(self):
        from spaiOS.core.summarizer import summarize_session
        result = summarize_session([])
        assert result == ""

    def test_calls_ollama_with_user_and_assistant_turns(self):
        from spaiOS.core.summarizer import summarize_session

        history = [
            {"role": "user", "content": "list my files"},
            {"role": "assistant", "content": "You have 3 files in sandbox."},
            {"role": "system", "content": "ignored system message"},
        ]
        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "User listed files in sandbox."}
            result = summarize_session(history)

        assert result == "User listed files in sandbox."
        call_prompt = mock_gen.call_args[1]["prompt"]
        assert "USER: list my files" in call_prompt
        assert "ASSISTANT: You have 3 files" in call_prompt
        assert "system" not in call_prompt.lower().split("conversation")[0]

    def test_strips_whitespace_from_response(self):
        from spaiOS.core.summarizer import summarize_session

        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "  Summary with spaces.  "}
            result = summarize_session([{"role": "user", "content": "hi"}])

        assert result == "Summary with spaces."

    def test_truncates_long_history_before_sending(self):
        from spaiOS.core.summarizer import summarize_session

        long_msg = "x" * 500
        history = [{"role": "user", "content": long_msg}] * 20

        with patch("ollama.generate") as mock_gen:
            mock_gen.return_value = {"response": "Short summary."}
            summarize_session(history)

        call_prompt = mock_gen.call_args[1]["prompt"]
        assert len(call_prompt) < 6000
