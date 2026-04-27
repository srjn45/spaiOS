# Task: Chrome App Control — CDP Connection + open_url

**Date:** 2026-04-27
**Phase:** Phase 2 — Milestone 2 (Chrome App Control)
**Session goal:** Connect to Chrome via Chrome DevTools Protocol (pychrome), implement
open_url and get_current_url, wire ChromeAgent into the Orchestrator tool loop, and
manually verify "hey Jarvis, open YouTube" navigates Chrome.
**Notion task:** phase2_m2_chrome_app_control

## What We're Building

A `ChromeAgent` that connects to a running Chrome instance via CDP on
`localhost:9222`. The agent can navigate to URLs, retrieve the current URL, and
fetch page text. It is wired as tools in the Orchestrator so the LLM can call them
when the user says "open X" or "go to X".

## Approach

1. `uv add pychrome` — lightweight pure-Python CDP client
2. Create `scripts/launch-chrome.sh` — launch Chrome with `--remote-debugging-port=9222`
3. Implement `src/spaiOS/agents/chrome_agent.py`:
   - `ChromeAgent.__init__` — connect to CDP, pick first tab
   - `is_available() -> bool` — True if debug port is open
   - `open_url(url: str) -> str` — navigate active tab; if Chrome not running, launch it
   - `get_current_url() -> str` — return current tab URL
   - `get_page_content() -> str` — return page body text (for LLM context)
4. Add `_CHROME_TOOLS` list in `orchestrator.py`
5. Extend `_BASE_SYSTEM_PROMPT` to mention Chrome tools
6. Extend `_dispatch_tool` to route `open_url`, `get_current_url`, `get_page_content`
7. Instantiate `ChromeAgent` inside `Orchestrator.__init__`
8. Manual test: say "hey Jarvis, open YouTube" → Chrome navigates to youtube.com
9. Run `uv run pytest` — all existing tests pass

## Files Touched

- `src/spaiOS/agents/chrome_agent.py` — new file
- `src/spaiOS/core/orchestrator.py` — add Chrome tools + dispatch
- `scripts/launch-chrome.sh` — new helper script
- `pyproject.toml` — add pychrome dep

## Done When

- [x] `ChromeAgent` connects to Chrome on port 9222
- [x] `open_url("https://youtube.com")` navigates Chrome to YouTube (code complete; manual test pending)
- [x] `get_current_url()` returns the current tab's URL
- [x] Orchestrator routes "open YouTube" → `open_url` tool call
- [x] Friendly error shown if Chrome isn't running with debug port (ChromeNotAvailable)
- [x] All existing pytest tests pass (49/49)
- [ ] Manual end-to-end voice test: "open YouTube" → Chrome navigates (next session)
