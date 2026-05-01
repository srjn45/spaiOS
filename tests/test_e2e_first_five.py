"""
E2E acceptance tests — "First Five" PRD scenarios (Phase 2, Milestone 5, Session 17).

Tests the complete flow: user prompt → Orchestrator.ask() → LLM dispatch → agent action.

Mocking strategy
----------------
- `spaiOS.core.llm.chat_with_tools` is replaced with a helper that calls
  `dispatch(tool_name, args)` directly, simulating a deterministic LLM tool call.
- External agent methods (Chrome CDP, PIL) are mocked at the instance level so tests
  control their return values without any network or GPU dependency.
- The workspace scenario uses a real FileAgent with a tmp_path sandbox, so actual
  directory creation is exercised.
"""

from unittest.mock import MagicMock, patch

from spaiOS.core.config import AppConfig
from spaiOS.core.orchestrator import Orchestrator

# ── helpers ────────────────────────────────────────────────────────────────────


def _config() -> AppConfig:
    return AppConfig()  # default: ollama provider


def _dispatch_caller(tool_name: str, tool_args: dict):
    """Return a chat_with_tools mock that calls dispatch once with the given tool call."""

    def _impl(messages, tools, dispatch, config):
        return dispatch(tool_name, tool_args)

    return _impl


def _text_responder(text: str):
    """Return a chat_with_tools mock that captures messages and returns a plain text reply."""
    captured: list[list[dict]] = []

    def _impl(messages, tools, dispatch, config):
        captured.append(list(messages))
        return text

    _impl.captured = captured  # type: ignore[attr-defined]
    return _impl


# ── S1: Open URL ───────────────────────────────────────────────────────────────


class TestScenario1OpenUrl:
    """'open youtube.com' → open_url dispatched → Chrome navigates."""

    def test_open_url_routes_to_chrome_agent(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.open_url = MagicMock(
            return_value="Navigated to https://youtube.com"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("open_url", {"url": "https://youtube.com"}),
        ):
            result = orc.ask("open youtube.com")

        orc._chrome_agent.open_url.assert_called_once_with("https://youtube.com")
        assert "youtube" in result.lower()

    def test_open_url_result_returned_to_user(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.open_url = MagicMock(
            return_value="Navigated to https://youtube.com"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("open_url", {"url": "https://youtube.com"}),
        ):
            result = orc.ask("open youtube.com")

        assert "Navigated" in result

    def test_chrome_unavailable_returns_friendly_error(self):
        from spaiOS.agents.chrome_agent import ChromeNotAvailable

        orc = Orchestrator(config=_config())
        orc._chrome_agent.open_url = MagicMock(
            side_effect=ChromeNotAvailable("not running")
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("open_url", {"url": "https://youtube.com"}),
        ):
            result = orc.ask("open youtube.com")

        assert "Chrome not available" in result or "not running" in result


# ── S2: Search Web ─────────────────────────────────────────────────────────────


class TestScenario2SearchWeb:
    """'search for lo-fi beats' → search_web dispatched → Chrome searches."""

    def test_search_web_routes_to_chrome_agent(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.search_web = MagicMock(
            return_value="Navigated to https://www.google.com/search?q=lo-fi+beats"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("search_web", {"query": "lo-fi beats"}),
        ):
            result = orc.ask("search for lo-fi beats on YouTube")

        orc._chrome_agent.search_web.assert_called_once_with("lo-fi beats")
        assert "google.com" in result or "lo-fi" in result.lower()

    def test_search_web_query_passed_through(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.search_web = MagicMock(return_value="Navigated to search")

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "search_web", {"query": "python async tutorial"}
            ),
        ):
            orc.ask("search for python async tutorial")

        orc._chrome_agent.search_web.assert_called_once_with("python async tutorial")


# ── S3: Memory Recall ─────────────────────────────────────────────────────────


class TestScenario3MemoryRecall:
    """'what have I been working on?' → session log injected into system prompt."""

    def _make_memory(self, summaries: list[str]) -> MagicMock:
        mem = MagicMock()
        mem.get_recent_sessions.return_value = summaries
        return mem

    def test_session_summaries_injected_into_system_prompt(self):
        memory = self._make_memory(
            ["Date: 2026-04-29\nSummary: Worked on voice pipeline wake-word detection."]
        )
        orc = Orchestrator(memory=memory, config=_config())

        responder = _text_responder(
            "You've been working on the voice pipeline wake-word detection."
        )
        with patch("spaiOS.core.llm.chat_with_tools", side_effect=responder):
            orc.ask("what have I been working on this week?")

        messages = responder.captured[0]
        system_content = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        assert "voice pipeline" in system_content

    def test_memory_answer_returned_to_user(self):
        memory = self._make_memory(
            ["Date: 2026-04-30\nSummary: Debugged media agent filter pipeline."]
        )
        orc = Orchestrator(memory=memory, config=_config())

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_text_responder(
                "You were debugging the media agent filter pipeline."
            ),
        ):
            result = orc.ask("what have I been working on?")

        assert "media agent" in result.lower() or "filter pipeline" in result.lower()

    def test_no_memory_gives_no_context_in_prompt(self):
        orc = Orchestrator(memory=None, config=_config())

        responder = _text_responder("I don't have any session history to reference.")
        with patch("spaiOS.core.llm.chat_with_tools", side_effect=responder):
            orc.ask("what have I been working on?")

        messages = responder.captured[0]
        system_content = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        assert "Recent session history" not in system_content


# ── S4: Photo Filter ──────────────────────────────────────────────────────────


class TestScenario4PhotoFilter:
    """'make this photo look like a 90s film' → apply_filter dispatched."""

    def test_apply_filter_routes_to_media_agent(self):
        orc = Orchestrator(config=_config())
        orc._media_agent.apply_filter = MagicMock(
            return_value="/tmp/photo_90s_film.jpg"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "apply_filter",
                {"image_path": "/tmp/photo.jpg", "style": "90s_film"},
            ),
        ):
            result = orc.ask(
                "make this photo look like a 90s film, path is /tmp/photo.jpg"
            )

        orc._media_agent.apply_filter.assert_called_once_with(
            "/tmp/photo.jpg", "90s_film"
        )
        assert "90s_film" in result or "saved to" in result.lower()

    def test_filter_output_path_in_result(self):
        orc = Orchestrator(config=_config())
        orc._media_agent.apply_filter = MagicMock(
            return_value="/tmp/photo_90s_film.jpg"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "apply_filter",
                {"image_path": "/tmp/photo.jpg", "style": "90s_film"},
            ),
        ):
            result = orc.ask("make this photo look like a 90s film")

        assert "/tmp/photo_90s_film.jpg" in result

    def test_vintage_filter_dispatches_correctly(self):
        orc = Orchestrator(config=_config())
        orc._media_agent.apply_filter = MagicMock(
            return_value="/tmp/sunset_vintage.jpg"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "apply_filter",
                {"image_path": "/tmp/sunset.jpg", "style": "vintage"},
            ),
        ):
            orc.ask("apply a vintage filter to /tmp/sunset.jpg")

        orc._media_agent.apply_filter.assert_called_once_with(
            "/tmp/sunset.jpg", "vintage"
        )


# ── S5: Workspace Setup ───────────────────────────────────────────────────────


class TestScenario5WorkspaceSetup:
    """'set up a workspace for the Tokyo project' → create_folder dispatched, real fs created."""

    def test_create_folder_routes_to_file_agent(self, tmp_path):
        from spaiOS.agents.file_agent import FileAgent

        orc = Orchestrator(config=_config())
        orc._file_agent = FileAgent(sandbox_path=str(tmp_path))

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("create_folder", {"subpath": "tokyo-project"}),
        ):
            result = orc.ask("set up a workspace for the Tokyo project")

        assert (tmp_path / "tokyo-project").is_dir()
        assert "Created" in result

    def test_multiple_subfolders_can_be_created(self, tmp_path):
        from spaiOS.agents.file_agent import FileAgent

        orc = Orchestrator(config=_config())
        orc._file_agent = FileAgent(sandbox_path=str(tmp_path))

        for subpath in ("tokyo-project", "tokyo-project/docs", "tokyo-project/src"):
            with patch(
                "spaiOS.core.llm.chat_with_tools",
                side_effect=_dispatch_caller("create_folder", {"subpath": subpath}),
            ):
                orc.ask(f"create folder {subpath}")

        assert (tmp_path / "tokyo-project" / "docs").is_dir()
        assert (tmp_path / "tokyo-project" / "src").is_dir()

    def test_workspace_result_mentions_folder_name(self, tmp_path):
        from spaiOS.agents.file_agent import FileAgent

        orc = Orchestrator(config=_config())
        orc._file_agent = FileAgent(sandbox_path=str(tmp_path))

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("create_folder", {"subpath": "tokyo-project"}),
        ):
            result = orc.ask("set up a workspace for the Tokyo project")

        assert "tokyo-project" in result


# ── AC3: Age-Gate Click ───────────────────────────────────────────────────────


class TestScenario3AgeGate:
    """'confirm I'm above 18' on an age-gate page → click_element dispatched."""

    def test_age_gate_routes_click_element_to_chrome_agent(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.click_element = MagicMock(
            return_value="Clicked element: #age-confirm-btn"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "click_element", {"selector": "#age-confirm-btn"}
            ),
        ):
            result = orc.ask("confirm I'm above 18")

        orc._chrome_agent.click_element.assert_called_once_with("#age-confirm-btn")
        assert "Clicked" in result

    def test_age_gate_result_includes_selector(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.click_element = MagicMock(
            return_value="Clicked element: .age-gate-confirm"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "click_element", {"selector": ".age-gate-confirm"}
            ),
        ):
            result = orc.ask("click the confirm button on this page")

        assert ".age-gate-confirm" in result

    def test_element_not_found_returns_friendly_message(self):
        orc = Orchestrator(config=_config())
        orc._chrome_agent.click_element = MagicMock(
            return_value="No element found matching: #age-confirm"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("click_element", {"selector": "#age-confirm"}),
        ):
            result = orc.ask("confirm I'm above 18")

        assert "No element found" in result or "#age-confirm" in result


# ── AC6: Open in Editor ───────────────────────────────────────────────────────


class TestScenario6OpenInEditor:
    """'open this file in the editor' → open_in_editor dispatched to CodeAgent."""

    def test_open_in_editor_routes_to_code_agent(self):
        orc = Orchestrator(config=_config())
        orc._code_agent.open_in_editor = MagicMock(
            return_value="Opened /home/srajan/spaiOS-sandbox/tokyo-project/main.py in editor"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "open_in_editor",
                {"path": "/home/srajan/spaiOS-sandbox/tokyo-project/main.py"},
            ),
        ):
            result = orc.ask(
                "open /home/srajan/spaiOS-sandbox/tokyo-project/main.py in the editor"
            )

        orc._code_agent.open_in_editor.assert_called_once_with(
            "/home/srajan/spaiOS-sandbox/tokyo-project/main.py"
        )
        assert "Opened" in result or "editor" in result.lower()

    def test_workspace_setup_then_open_editor(self, tmp_path):
        """Full workspace flow: create folder, then open a file in editor."""
        from spaiOS.agents.file_agent import FileAgent

        orc = Orchestrator(config=_config())
        orc._file_agent = FileAgent(sandbox_path=str(tmp_path))
        orc._code_agent.open_in_editor = MagicMock(
            return_value=f"Opened {tmp_path}/tokyo-project/main.py in editor"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("create_folder", {"subpath": "tokyo-project"}),
        ):
            orc.ask("set up a workspace for the Tokyo project")

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller(
                "open_in_editor",
                {"path": f"{tmp_path}/tokyo-project/main.py"},
            ),
        ):
            result = orc.ask("open the main.py file in the editor")

        assert (tmp_path / "tokyo-project").is_dir()
        orc._code_agent.open_in_editor.assert_called_once()
        assert "Opened" in result or "editor" in result.lower()

    def test_open_in_editor_result_returned_to_user(self):
        orc = Orchestrator(config=_config())
        orc._code_agent.open_in_editor = MagicMock(
            return_value="Opened /tmp/test.py in editor"
        )

        with patch(
            "spaiOS.core.llm.chat_with_tools",
            side_effect=_dispatch_caller("open_in_editor", {"path": "/tmp/test.py"}),
        ):
            result = orc.ask("open /tmp/test.py in the editor")

        assert "/tmp/test.py" in result


# ── S6: Config Switching (Anthropic) ─────────────────────────────────────────


class TestScenario6ConfigSwitching:
    """Switching config.toml provider to 'anthropic' routes through the Anthropic SDK path."""

    def test_anthropic_provider_calls_anthropic_chat(self):
        config = AppConfig(provider="anthropic")
        config.anthropic.api_key = "test-key"
        config.anthropic.model = "claude-haiku-4-5-20251001"

        orc = Orchestrator(config=config)
        orc._chrome_agent.open_url = MagicMock(
            return_value="Navigated to https://youtube.com"
        )

        with patch("spaiOS.core.llm._anthropic_chat") as mock_anthropic:
            mock_anthropic.return_value = "Navigated to https://youtube.com"
            result = orc.ask("open youtube.com")

        mock_anthropic.assert_called_once()
        assert "youtube" in result.lower() or "Navigated" in result

    def test_ollama_provider_calls_ollama_chat(self):
        config = AppConfig(provider="ollama")
        orc = Orchestrator(config=config)

        with patch("spaiOS.core.llm._ollama_chat") as mock_ollama:
            mock_ollama.return_value = "Done."
            orc.ask("hello")

        mock_ollama.assert_called_once()

    def test_openai_provider_calls_openai_chat(self):
        config = AppConfig(provider="openai")
        config.openai.api_key = "test-key"
        orc = Orchestrator(config=config)

        with patch("spaiOS.core.llm._openai_chat") as mock_openai:
            mock_openai.return_value = "Done."
            orc.ask("hello")

        mock_openai.assert_called_once()
