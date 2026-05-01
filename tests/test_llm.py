from unittest.mock import MagicMock, patch

import pytest

from spaiOS.core.config import AppConfig, AnthropicConfig, OpenAIConfig
from spaiOS.core.llm import _to_anthropic_tools, chat_with_tools


def _ollama_cfg() -> AppConfig:
    cfg = AppConfig()
    cfg.provider = "ollama"
    return cfg


def _anthropic_cfg() -> AppConfig:
    cfg = AppConfig()
    cfg.provider = "anthropic"
    cfg.anthropic = AnthropicConfig(
        api_key="sk-test", model="claude-haiku-4-5-20251001"
    )
    return cfg


def _openai_cfg() -> AppConfig:
    cfg = AppConfig()
    cfg.provider = "openai"
    cfg.openai = OpenAIConfig(api_key="sk-test", model="gpt-4o-mini")
    return cfg


# ── _to_anthropic_tools ────────────────────────────────────────────────────────


def test_to_anthropic_tools_conversion():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        }
    ]
    result = _to_anthropic_tools(tools)
    assert len(result) == 1
    assert result[0]["name"] == "list_files"
    assert result[0]["description"] == "List files."
    assert "input_schema" in result[0]
    assert result[0]["input_schema"]["properties"]["path"]["type"] == "string"


# ── Ollama routing ─────────────────────────────────────────────────────────────


def test_ollama_simple_reply():
    mock_msg = MagicMock()
    mock_msg.tool_calls = []
    mock_msg.content = "Hello from Ollama"
    mock_response = MagicMock()
    mock_response.message = mock_msg

    with patch("spaiOS.core.llm.ollama") as mock_ollama:
        mock_ollama.chat.return_value = mock_response
        result = chat_with_tools(
            [{"role": "user", "content": "hi"}],
            [],
            lambda name, args: "",
            config=_ollama_cfg(),
        )

    assert result == "Hello from Ollama"


def test_ollama_tool_call_then_reply():
    tc = MagicMock()
    tc.function.name = "list_directory"
    tc.function.arguments = {"subpath": ""}

    msg_with_tool = MagicMock()
    msg_with_tool.tool_calls = [tc]
    msg_with_tool.content = None

    msg_final = MagicMock()
    msg_final.tool_calls = []
    msg_final.content = "Here are your files."

    response_tool = MagicMock()
    response_tool.message = msg_with_tool

    response_final = MagicMock()
    response_final.message = msg_final

    dispatched = []

    def dispatch(name, args):
        dispatched.append((name, args))
        return "file1.txt\nfile2.txt"

    with patch("spaiOS.core.llm.ollama") as mock_ollama:
        mock_ollama.chat.side_effect = [response_tool, response_final]
        result = chat_with_tools(
            [{"role": "user", "content": "list files"}],
            [],
            dispatch,
            config=_ollama_cfg(),
        )

    assert result == "Here are your files."
    assert dispatched == [("list_directory", {"subpath": ""})]


# ── Anthropic routing ──────────────────────────────────────────────────────────


def test_anthropic_simple_reply():
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Hello from Anthropic"

    mock_response = MagicMock()
    mock_response.content = [text_block]
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("spaiOS.core.llm.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        result = chat_with_tools(
            [{"role": "user", "content": "hi"}],
            [],
            lambda name, args: "",
            config=_anthropic_cfg(),
        )

    assert result == "Hello from Anthropic"


def test_anthropic_tool_call_then_reply():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "toolu_01"
    tool_block.name = "list_directory"
    tool_block.input = {"subpath": ""}

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Done."

    response_tool = MagicMock()
    response_tool.content = [tool_block]
    response_tool.stop_reason = "tool_use"

    response_final = MagicMock()
    response_final.content = [text_block]
    response_final.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [response_tool, response_final]

    dispatched = []

    def dispatch(name, args):
        dispatched.append((name, args))
        return "files"

    with patch("spaiOS.core.llm.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        result = chat_with_tools(
            [{"role": "user", "content": "list files"}],
            [],
            dispatch,
            config=_anthropic_cfg(),
        )

    assert result == "Done."
    assert dispatched == [("list_directory", {"subpath": ""})]


def test_anthropic_system_message_separated():
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "OK"

    mock_response = MagicMock()
    mock_response.content = [text_block]
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("spaiOS.core.llm.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        chat_with_tools(
            [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "hi"},
            ],
            [],
            lambda name, args: "",
            config=_anthropic_cfg(),
        )
        call_kwargs = mock_client.messages.create.call_args[1]

    assert call_kwargs["system"] == "You are helpful."
    assert all(m["role"] != "system" for m in call_kwargs["messages"])


# ── OpenAI routing ─────────────────────────────────────────────────────────────


def test_openai_simple_reply():
    mock_msg = MagicMock()
    mock_msg.tool_calls = None
    mock_msg.content = "Hello from OpenAI"

    mock_choice = MagicMock()
    mock_choice.message = mock_msg

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("spaiOS.core.llm.openai") as mock_openai:
        mock_openai.OpenAI.return_value = mock_client
        mock_openai.NOT_GIVEN = None
        result = chat_with_tools(
            [{"role": "user", "content": "hi"}],
            [],
            lambda name, args: "",
            config=_openai_cfg(),
        )

    assert result == "Hello from OpenAI"


# ── Loop interrupt propagation ─────────────────────────────────────────────────


def test_loop_interrupt_propagates_from_dispatch():
    from spaiOS.core.orchestrator import _LoopInterrupt

    msg_with_tool = MagicMock()
    tc = MagicMock()
    tc.function.name = "write_file"
    tc.function.arguments = {}
    msg_with_tool.tool_calls = [tc]

    mock_response = MagicMock()
    mock_response.message = msg_with_tool

    def dispatch_raises(name, args):
        raise _LoopInterrupt("diff shown, confirm?")

    with patch("spaiOS.core.llm.ollama") as mock_ollama:
        mock_ollama.chat.return_value = mock_response
        with pytest.raises(_LoopInterrupt) as exc_info:
            chat_with_tools(
                [{"role": "user", "content": "write file"}],
                [],
                dispatch_raises,
                config=_ollama_cfg(),
            )

    assert "confirm" in exc_info.value.message
