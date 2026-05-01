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
