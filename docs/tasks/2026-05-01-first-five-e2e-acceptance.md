# Task: "First Five" PRD Scenarios — E2E Acceptance Tests

**Date:** 2026-05-01
**Phase:** Phase 2 — Milestone 5 (Remaining Agents + Config)
**Session goal:** Write E2E acceptance tests that verify all five core PRD scenarios route correctly end-to-end through the Orchestrator.
**Notion task ID:** phase2_m5_agents_config

## What We're Building

A new test file (`tests/test_e2e_first_five.py`) that covers the five showcase scenarios that define Phase 2's value: web navigation, web search, memory recall, photo filtering, and workspace setup. A sixth test verifies the Anthropic config-switching path.

## Approach

1. Mock `spaiOS.core.llm.chat_with_tools` to simulate deterministic LLM tool calls without requiring Ollama or any API key.
2. Mock external agent methods (Chrome CDP, MediaAgent PIL ops) at the object level, so the test controls what they return without network or disk access.
3. For the workspace scenario use a real `FileAgent` with `tmp_path` — exercises actual folder creation.
4. For the memory scenario capture the `messages` argument to `chat_with_tools` and assert the session summary was injected into the system prompt.
5. For config switching, stub the Anthropic client and assert `_anthropic_chat` is entered.

## Files Touched

- `tests/test_e2e_first_five.py` — new file (all tests)

## Done When

- [ ] S1 — "open youtube.com" → `ChromeAgent.open_url` called with `https://youtube.com`; result contains "youtube"
- [ ] S2 — "search for lo-fi beats" → `ChromeAgent.search_web` called with "lo-fi beats"
- [ ] S3 — "what have I been working on?" → memory context present in system prompt; LLM text answer returned
- [ ] S4 — "make this photo look like a 90s film" → `MediaAgent.apply_filter` called with `style="90s_film"`; output path in result
- [ ] S5 — "set up a workspace for the Tokyo project" → folder created in tmp sandbox; result mentions creation
- [ ] S6 — Anthropic config → `llm._anthropic_chat` path exercised (mocked client)
- [ ] All 144 existing tests still pass after adding new file
