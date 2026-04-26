# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 5, Session 14

**Goal:** End-to-end smoke test and polish — run the overlay live, test "list my sandbox files" and "organize my sandbox", verify the delete confirmation flow, fix any rough edges.

**Steps (in order):**
1. Create test files in `~/spaiOS-sandbox/` (mix of types: .txt, .py, images, etc.)
2. Launch overlay: `spaiOS`
3. Test "list my sandbox files" → confirm AI calls list_directory and shows a listing
4. Test "organize my sandbox" → AI creates folders, moves files; check they land correctly
5. Test delete flow: ask AI to delete a file → confirm amber sphere + "yes/no" prompt → type "yes" → confirm deletion; type "no" → confirm cancellation
6. Test "read summary of <file>" → AI shows file preview
7. Tune system prompt if model isn't picking up tools reliably (add explicit instruction to use tools for file tasks)
8. Commit any fixes

**Notion task:** phase1_m5_file_agent (same task)
**Task doc:** `docs/tasks/2026-04-27-m5-e2e-smoke.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
