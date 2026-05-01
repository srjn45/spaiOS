# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 2, Session 9 (E2E Browser Tests)

**Goal:** Manual E2E validation of the full Browser Agent — age-gate scenario, multi-field form
fill, tab listing. Then mark Milestone 2 complete and prep Phase 2 Milestone 3.

**Notion task:** phase2_m2_chrome_app_control

**Done last session (Session 8):**
- `fill_form`, `click_link_by_text`, `get_tabs`, `clear_history` added to ChromeAgent
- All four tools wired into Orchestrator (tool defs + dispatch + system prompt)
- 68/68 tests pass

**Steps (in order):**
1. Launch Chrome + spaiOS
2. E2E: say "fill in the search box with 'lo-fi beats' and submit" — verify fill_form works
3. E2E: say "click the Wikipedia link" on a Google results page — verify click_link_by_text
4. E2E: say "what tabs do I have open" — verify get_tabs returns tab URLs
5. E2E: age-gate scenario on any age-gated site — verify click_link_by_text on confirm button
6. If all pass: update Notion task to done, read phase doc and plan Milestone 3

**Known risks:**
- `click_link_by_text` may time out on pages with hundreds of links (large DOM)
- CDP `History.deleteAll` may not be supported in all Chrome builds
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
