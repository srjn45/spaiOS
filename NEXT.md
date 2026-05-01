# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 2, Session 8 (Full Browser Agent)

**Goal:** Complete the Browser Agent — wrap all CDP tools in intent-oriented functions
(`click_link_by_text`, `fill_form`, `get_tabs`, `clear_history`), then wire them into
Orchestrator. Manual E2E: age-gate scenario + multi-field form fill.

**Notion task:** phase2_m2_chrome_app_control

**Done last session (Session 7):**
- `fill_input(selector, value)` added to ChromeAgent (native value setter + input/change events)
- `fill_input` tool registered in Orchestrator + system prompt updated
- 58/58 tests pass

**Steps (in order):**
1. Add `fill_form(fields: dict[str, str])` to ChromeAgent (calls fill_input per field)
2. Add `click_link_by_text(link_text: str)` to ChromeAgent (querySelector by text content)
3. Add `get_tabs() -> list` and `clear_history()` to ChromeAgent
4. Wire all four tools into Orchestrator (_CHROME_TOOLS + dispatch + system prompt)
5. Write tests for new methods
6. Manual E2E: launch Chrome + spaiOS, say "fill in the search box with 'lo-fi beats' and submit"
7. Manual E2E: age-gate scenario on any age-gated site

**Known risks:**
- `click_link_by_text` requires iterating anchors by innerText — may be slow on large pages
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
