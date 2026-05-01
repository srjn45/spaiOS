# Task: fill_input + age-gate scenario

**Date:** 2026-05-01
**Phase:** Phase 2 — The Reach
**Session goal:** Add fill_input to ChromeAgent, wire into Orchestrator, cover with tests.
**Notion task ID:** phase2_m2_chrome_app_control

## What We're Building

`fill_input(selector, value)` — sets the value of a form input in the active Chrome tab
by CSS selector, dispatching input/change events so JS-driven forms respond correctly.
This completes the interaction toolkit needed for the age-gate scenario.

## Approach

1. Add `fill_input(selector, value)` method to `ChromeAgent` (JS via CDP Runtime.evaluate)
2. Add `fill_input` tool definition to `_CHROME_TOOLS` in Orchestrator
3. Dispatch `fill_input` in `Orchestrator._dispatch_tool`
4. Update `_BASE_SYSTEM_PROMPT` to mention `fill_input` and `click_element`
5. Add unit tests for `fill_input` logic in a new `tests/test_chrome_agent.py`
6. Run full test suite — 49 existing + new tests must pass

## Files Touched

- `src/spaiOS/agents/chrome_agent.py` — add fill_input method
- `src/spaiOS/core/orchestrator.py` — tool definition + dispatch + system prompt
- `tests/test_chrome_agent.py` — new test file for ChromeAgent unit tests

## Done When

- `ChromeAgent.fill_input(selector, value)` returns "Filled <selector>" on success
- `ChromeAgent.fill_input` returns "No element found for selector: <selector>" when element missing
- Orchestrator dispatches `fill_input` tool correctly
- System prompt mentions fill_input and click_element
- All tests pass (existing 49 + new ones)
