# Task: Full Browser Agent

**Date:** 2026-05-01
**Phase:** Phase 2 — The Reach, Milestone 2
**Session goal:** Complete ChromeAgent with fill_form, click_link_by_text, get_tabs, clear_history — wire all into Orchestrator with tests.
**Notion task ID:** phase2_m2_chrome_app_control

## What We're Building

Four new intent-oriented methods on ChromeAgent that sit above the raw CDP primitives.
`fill_form` batches `fill_input` calls. `click_link_by_text` finds anchor tags by text.
`get_tabs` lists all open CDP tabs. `clear_history` clears Chrome browsing history via CDP.

## Approach

1. Add `fill_form(fields: dict[str, str])` — iterates fields, calls fill_input per entry
2. Add `click_link_by_text(link_text: str)` — iterates anchors, matches trimmed innerText
3. Add `get_tabs() -> list[str]` — calls `_browser.list_tab()` and returns URL list
4. Add `clear_history()` — uses `History.deleteAll()` via CDP
5. Wire all four into `_CHROME_TOOLS` + `_dispatch_tool` + system prompt in orchestrator
6. Add tests for all four methods
7. Run full test suite (58 + new tests must all pass)
8. Manual E2E: fill_form on a multi-field form, click_link_by_text on Google results

## Files Touched

- `src/spaiOS/agents/chrome_agent.py` — four new methods
- `src/spaiOS/core/orchestrator.py` — tool defs + dispatch + system prompt
- `tests/test_chrome_agent.py` — tests for new methods

## Done When

- `fill_form({"input[name='q']": "lo-fi", "#submit": ""})` fills both fields
- `click_link_by_text("Wikipedia")` clicks the first link whose text matches
- `get_tabs()` returns a list of URL strings
- `clear_history()` succeeds (or returns friendly error if CDP call fails)
- All tests pass
