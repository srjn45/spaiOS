# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 7, Session 16

**Goal:** End-to-end polish + Phase 1 wrap — smoke-test the full overlay flow, fix any
remaining rough edges, and close out Phase 1 with a clean commit and Notion sync.

**Steps (in order):**
1. Run `python src/main.py` and manually test: idle → question → file list → move → delete confirmation
2. Test `/clear` resets context mid-session correctly
3. Test Escape cancels in-flight requests without clearing history prematurely
4. Fix any bugs found during manual testing
5. Update phase doc to mark Phase 1 complete
6. Sync docs/ changes to Notion
7. Commit

**Notion task:** phase1_m7_wrap
**Task doc:** `docs/tasks/YYYY-MM-DD-m7-wrap.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
