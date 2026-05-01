from __future__ import annotations

import json
from collections.abc import Callable

import anthropic
import ollama
import openai

from spaiOS.core.config import AppConfig, load_config

_TOOL_LOOP_LIMIT = 10


def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    dispatch: Callable[[str, dict], str],
    config: AppConfig | None = None,
) -> str:
    if config is None:
        config = load_config()

    if config.provider == "anthropic":
        return _anthropic_chat(messages, tools, dispatch, config)
    if config.provider == "openai":
        return _openai_chat(messages, tools, dispatch, config)
    return _ollama_chat(messages, tools, dispatch, config)


def _ollama_chat(
    messages: list[dict],
    tools: list[dict],
    dispatch: Callable[[str, dict], str],
    config: AppConfig,
) -> str:
    loop_messages = list(messages)
    model = config.ollama.model

    for _ in range(_TOOL_LOOP_LIMIT):
        response = ollama.chat(model=model, messages=loop_messages, tools=tools)
        msg = response.message

        if not msg.tool_calls:
            return msg.content or ""

        loop_messages.append(msg)

        for tc in msg.tool_calls:
            result = dispatch(tc.function.name, tc.function.arguments or {})
            loop_messages.append({"role": "tool", "content": result})

    return "I reached the tool call limit — please try a simpler request."


def _to_anthropic_tools(tools: list[dict]) -> list[dict]:
    return [
        {
            "name": t["function"]["name"],
            "description": t["function"].get("description", ""),
            "input_schema": t["function"].get(
                "parameters", {"type": "object", "properties": {}}
            ),
        }
        for t in tools
    ]


def _anthropic_chat(
    messages: list[dict],
    tools: list[dict],
    dispatch: Callable[[str, dict], str],
    config: AppConfig,
) -> str:
    client = anthropic.Anthropic(api_key=config.anthropic.api_key)
    model = config.anthropic.model
    anthropic_tools = _to_anthropic_tools(tools)

    system = ""
    conv_messages: list[dict] = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            conv_messages.append({"role": m["role"], "content": m["content"]})

    loop_messages = list(conv_messages)

    for _ in range(_TOOL_LOOP_LIMIT):
        kwargs: dict = dict(
            model=model,
            max_tokens=4096,
            messages=loop_messages,
            tools=anthropic_tools,
        )
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            text_blocks = [b for b in response.content if b.type == "text"]
            return text_blocks[0].text if text_blocks else ""

        loop_messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            result = dispatch(block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            )
        loop_messages.append({"role": "user", "content": tool_results})

    return "I reached the tool call limit — please try a simpler request."


def _openai_chat(
    messages: list[dict],
    tools: list[dict],
    dispatch: Callable[[str, dict], str],
    config: AppConfig,
) -> str:
    client = openai.OpenAI(
        api_key=config.openai.api_key, base_url=config.openai.base_url
    )
    model = config.openai.model
    loop_messages = list(messages)

    for _ in range(_TOOL_LOOP_LIMIT):
        response = client.chat.completions.create(
            model=model,
            messages=loop_messages,
            tools=tools or openai.NOT_GIVEN,
        )

        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return msg.content or ""

        loop_messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = dispatch(tc.function.name, args)
            loop_messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )

    return "I reached the tool call limit — please try a simpler request."
