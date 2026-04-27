# Task: Add search_web Tool + E2E Voice Flow Verification

**Date:** 2026-04-27
**Phase:** Phase 2 — The Reach
**Session goal:** Verify "open YouTube" voice flow end-to-end, then add search_web(query) tool so "search for X" voice commands navigate Chrome to Google results.
**Notion task ID:** phase2_m2_chrome_app_control

## What We're Building

A `search_web(query)` tool on `ChromeAgent` that constructs a Google search URL and
delegates to `open_url`. The Orchestrator exposes this as a tool in the LLM tool loop
so voice commands like "search for lo-fi beats" navigate Chrome to Google results.

## Approach

1. Add `search_web(query: str) -> str` to `ChromeAgent` — constructs Google URL, calls `open_url`
2. Register `search_web` tool definition in `Orchestrator._build_tools()`
3. Add dispatch branch in `Orchestrator._call_tool()` for `search_web`
4. Update system prompt to include `search_web` description
5. Run `uv run pytest` — all pass
6. Manual E2E: launch Chrome → launch spaiOS → say "open YouTube" → verify nav
7. Manual E2E: say "search for lo-fi beats" → verify Google search results

## Files Touched

- `src/spaiOS/agents/chrome_agent.py` — add `search_web` method
- `src/spaiOS/core/orchestrator.py` — register tool + dispatch + system prompt update

## Done When

- [ ] `search_web` constructs correct Google URL and calls `open_url`
- [ ] Orchestrator exposes it as a tool the LLM can call
- [ ] All existing tests pass (`uv run pytest`)
- [ ] Manual: "open YouTube" navigates Chrome to youtube.com
- [ ] Manual: "search for lo-fi beats" opens Google results in Chrome
