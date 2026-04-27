# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 2 (Chrome App Control)

**Goal:** Let the user say "hey Jarvis, open YouTube" or "go to gmail" and have
spaiOS control the Chrome browser via CDP or xdotool — launching it, navigating
to URLs, and clicking elements by voice command.

**Notion task:** phase2_m2_chrome_app_control

**Steps (in order):**
1. Research control approach: Chrome DevTools Protocol (CDP) via `pychrome` or
   `playwright`, vs. xdotool/AT-SPI for simpler URL navigation
2. Write task doc: `docs/tasks/2026-04-27-p2-chrome-app-control.md`
3. Implement `ChromeAgent` in `src/spaiOS/agents/chrome_agent.py`
   - open_url(url: str) — launch Chrome or navigate existing window
   - click_element(selector: str) — click by CSS selector via CDP
4. Wire ChromeAgent as a tool in the Orchestrator tool-calling loop
5. Add intent parsing: map "open X" / "go to X" voice commands to open_url
6. Manual test: say "hey Jarvis, open YouTube" → Chrome opens youtube.com
7. Run `uv run pytest` — all pass

**Known risks:**
- Chrome needs to be launched with `--remote-debugging-port=9222` for CDP
- Fall back to `xdg-open` if Chrome isn't running and CDP unavailable
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
