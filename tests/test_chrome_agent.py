import json
from unittest.mock import MagicMock, patch

from spaiOS.agents.chrome_agent import ChromeAgent


def _make_agent_connected() -> ChromeAgent:
    """Return a ChromeAgent with a mocked _tab already connected."""
    agent = ChromeAgent()
    agent._browser = MagicMock()
    agent._tab = MagicMock()
    return agent


def _runtime_result(value) -> dict:
    return {"result": {"value": value}}


# ── click_element ──────────────────────────────────────────────────────────────


class TestClickElement:
    def test_click_found_element(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("clicked")
        result = agent.click_element("#submit-btn")
        assert result == "Clicked element: #submit-btn"

    def test_click_element_not_found(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("not_found")
        result = agent.click_element("#missing")
        assert "No element found" in result
        assert "#missing" in result

    def test_click_element_selector_passed_to_js(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("clicked")
        agent.click_element(".age-confirm")
        call_expr = agent._tab.Runtime.evaluate.call_args[1]["expression"]
        assert ".age-confirm" in call_expr


# ── fill_input ─────────────────────────────────────────────────────────────────


class TestFillInput:
    def test_fill_found_input(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("filled")
        result = agent.fill_input("input[name='q']", "lo-fi beats")
        assert result == "Filled input[name='q']"

    def test_fill_input_not_found(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("not_found")
        result = agent.fill_input("#nonexistent", "hello")
        assert "No element found" in result
        assert "#nonexistent" in result

    def test_fill_input_passes_selector_and_value_to_js(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("filled")
        agent.fill_input("#search", "test query")
        call_expr = agent._tab.Runtime.evaluate.call_args[1]["expression"]
        assert "#search" in call_expr
        assert "test query" in call_expr

    def test_fill_input_dispatches_events(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("filled")
        agent.fill_input("#q", "value")
        call_expr = agent._tab.Runtime.evaluate.call_args[1]["expression"]
        assert "dispatchEvent" in call_expr
        assert "input" in call_expr
        assert "change" in call_expr


# ── fill_form ──────────────────────────────────────────────────────────────────


class TestFillForm:
    def test_fills_all_fields(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("filled")
        result = agent.fill_form({"input[name='q']": "lo-fi", "#city": "London"})
        assert "Filled input[name='q']" in result
        assert "Filled #city" in result

    def test_empty_fields_returns_empty_string(self):
        agent = _make_agent_connected()
        result = agent.fill_form({})
        assert result == ""

    def test_calls_fill_input_per_field(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("filled")
        agent.fill_form({"#a": "1", "#b": "2"})
        assert agent._tab.Runtime.evaluate.call_count == 2


# ── click_link_by_text ─────────────────────────────────────────────────────────


def _mock_urlopen(tabs_data: list) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(tabs_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestClickLinkByText:
    def test_click_found_link(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("clicked:Wikipedia")
        result = agent.click_link_by_text("Wikipedia")
        assert "Wikipedia" in result
        assert "Clicked" in result

    def test_link_not_found(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("not_found")
        result = agent.click_link_by_text("Nonexistent")
        assert "No link or button found" in result
        assert "Nonexistent" in result

    def test_link_text_lowercased_in_js(self):
        agent = _make_agent_connected()
        agent._tab.Runtime.evaluate.return_value = _runtime_result("clicked:Wikipedia")
        agent.click_link_by_text("Wikipedia")
        expr = agent._tab.Runtime.evaluate.call_args[1]["expression"]
        assert "wikipedia" in expr


# ── get_tabs ───────────────────────────────────────────────────────────────────


class TestGetTabs:
    def test_returns_tab_urls(self):
        agent = _make_agent_connected()
        tabs = [
            {"type": "page", "url": "https://google.com"},
            {"type": "page", "url": "https://youtube.com"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(tabs)):
            result = agent.get_tabs()
        assert result == ["https://google.com", "https://youtube.com"]

    def test_returns_empty_list_when_no_tabs(self):
        agent = _make_agent_connected()
        with patch("urllib.request.urlopen", return_value=_mock_urlopen([])):
            result = agent.get_tabs()
        assert result == []

    def test_filters_non_page_tabs(self):
        agent = _make_agent_connected()
        tabs = [
            {"type": "page", "url": "https://google.com"},
            {"type": "background_page", "url": "chrome-extension://abc/bg.html"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(tabs)):
            result = agent.get_tabs()
        assert result == ["https://google.com"]


# ── clear_history ──────────────────────────────────────────────────────────────


class TestClearHistory:
    def test_returns_success_message(self):
        agent = _make_agent_connected()
        agent._tab.History.deleteAll.return_value = None
        result = agent.clear_history()
        assert result == "Browsing history cleared"

    def test_returns_error_message_on_exception(self):
        agent = _make_agent_connected()
        agent._tab.History.deleteAll.side_effect = Exception("not supported")
        result = agent.clear_history()
        assert "Could not clear history" in result
        assert "not supported" in result


# ── is_available ───────────────────────────────────────────────────────────────


class TestIsAvailable:
    def test_returns_true_when_port_open(self):
        agent = ChromeAgent()
        with patch("urllib.request.urlopen"):
            assert agent.is_available() is True

    def test_returns_false_when_port_closed(self):
        agent = ChromeAgent()
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            assert agent.is_available() is False
