# Task: MCP Config System — Provider Switching

**Date:** 2026-05-01
**Phase:** Phase 2 — The Reach
**Session goal:** Add config.toml provider switching so the Orchestrator routes LLM calls to Ollama, Anthropic, or OpenAI based on user config.
**Notion task ID:** phase2_m5_agents_config

## What We're Building

A thin config layer (`config.py`) that reads `config.toml` and a provider abstraction (`llm.py`) that dispatches `chat_with_tools` calls to the right backend. The Orchestrator stops calling `ollama.chat` directly and instead calls `llm.chat_with_tools`, which handles Ollama, Anthropic, and OpenAI tool loops natively.

## Approach

1. Create `config.example.toml` — committed template with no secrets
2. Create `src/spaiOS/core/config.py` — dataclasses + loader using stdlib `tomllib`
3. Create `src/spaiOS/core/llm.py` — `chat_with_tools(messages, tools, dispatch, config)` for all three providers
4. Add `anthropic` and `openai` to `pyproject.toml` deps
5. Refactor `orchestrator.py` — load config once, use `llm.chat_with_tools`, move loop interrupt to `_LoopInterrupt` exception
6. Add `tests/test_config.py` and `tests/test_llm.py`
7. Run lint + tests

## Files Touched

- `config.example.toml` — new, safe template
- `src/spaiOS/core/config.py` — new, AppConfig + load_config()
- `src/spaiOS/core/llm.py` — new, chat_with_tools() for all providers
- `src/spaiOS/core/orchestrator.py` — use config + llm module, remove hardcoded model constants
- `pyproject.toml` — add anthropic, openai deps
- `tests/test_config.py` — new
- `tests/test_llm.py` — new
- `tests/test_orchestrator.py` — update import (emit_ollama_error → emit_llm_error)

## Done When

- `load_config()` returns `AppConfig` defaults when no config.toml is present
- `load_config()` reads provider/ollama/anthropic/openai sections correctly
- `llm.chat_with_tools` routes to Ollama when `provider = "ollama"` (default)
- `llm.chat_with_tools` routes to Anthropic when `provider = "anthropic"`
- `llm.chat_with_tools` routes to OpenAI when `provider = "openai"`
- Orchestrator no longer imports `ollama` at module level (lazy import in llm.py)
- `WriteConfirmationRequired` and `DeleteConfirmationRequired` still interrupt the loop correctly
- All existing 129 tests pass + new config/llm tests added
