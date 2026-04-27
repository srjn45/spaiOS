# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 2, Session 6 (Chrome URL + Content tools)

**Goal:** Verify the full "open YouTube" voice flow end-to-end with Chrome running
on the debug port. Then add `search_web` intent (voice → search query → Chrome
navigates to search results) and test `get_page_content` summarisation.

**Notion task:** phase2_m2_chrome_app_control

**Done last session (Session 5):**
- `pychrome` installed, `ChromeAgent` implemented (open_url, get_current_url,
  get_page_content, click_element)
- `scripts/launch-chrome.sh` created
- ChromeAgent wired into Orchestrator tool loop
- 49/49 tests pass

**Steps (in order):**
1. Launch Chrome: `bash scripts/launch-chrome.sh`
2. Launch spaiOS: `spaiOS`
3. Manual test: say "open YouTube" → Chrome navigates to youtube.com
4. Manual test: say "what's on this page?" → overlay summarises page content
5. If open_url fails: debug pychrome connection; check Chrome was launched with port 9222
6. Add `search_web(query)` tool to ChromeAgent + orchestrator:
   - Constructs `https://www.google.com/search?q=<query>` and calls open_url
7. Manual test: "search for lo-fi beats" → Chrome opens Google search results
8. Run `uv run pytest` — all pass
9. Update task doc with results

**Known risks:**
- Chrome debug port may need a fresh Chrome launch (existing profiles block `--remote-debugging-port`)
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
