# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 2, Session 7 (Manual E2E voice flows)

**Goal:** Run the full manual E2E voice flows: "open YouTube", "what's on this page?",
and "search for lo-fi beats". Fix any pychrome connection issues if they surface.
Then determine the next milestone goal from the phase doc.

**Notion task:** phase2_m2_chrome_app_control

**Done last session (Session 6):**
- `search_web(query)` added to ChromeAgent (constructs Google URL, delegates to open_url)
- `search_web` tool registered in Orchestrator tool loop + system prompt updated
- 49/49 tests pass

**Steps (in order):**
1. Launch Chrome: `bash scripts/launch-chrome.sh`
2. Launch spaiOS: `spaiOS`
3. Manual test: say "open YouTube" → Chrome navigates to youtube.com
4. Manual test: say "what's on this page?" → overlay summarises page content
5. Manual test: say "search for lo-fi beats" → Chrome opens Google search results
6. If any step fails: debug pychrome connection; check Chrome was launched with port 9222
7. Check `docs/phases/2026-04-26-phase-2-the-reach.md` for next milestone after M2
8. Update this file with Session 8 goal

**Known risks:**
- Chrome debug port may need a fresh Chrome launch (existing profiles block `--remote-debugging-port`)
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
