# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 6, Session 15

**Goal:** Conversation memory + multi-turn context — the overlay should remember earlier turns in a session so follow-up questions ("and delete that one", "now move it to docs/") work correctly.

**Steps (in order):**
1. Review current `_history` handling in `orchestrator.py` — confirm multi-turn messages are threaded correctly
2. Test multi-turn file flows manually: list → "now move the .py file to a scripts folder" → "delete it"
3. Add a "clear history" button or `/clear` command to the overlay input so the user can reset context
4. Verify delete confirmation still works when the pending delete path comes from a prior turn
5. Commit

**Notion task:** phase1_m6_memory
**Task doc:** `docs/tasks/YYYY-MM-DD-m6-memory.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
