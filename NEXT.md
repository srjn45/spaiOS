# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 4, Session 10

**Goal:** Implement clarifying questions flow — AI can ask a follow-up question mid-task, overlay stays open for the user to answer, and the UI visually distinguishes "AI is asking" from "AI is responding."

**Steps (in order):**
1. Detect when the model's reply ends with a `?` (heuristic) or starts with a clarifying phrase — mark it as a "question" response
2. `src/spaiOS/ui/overlay.py` — when response is a question, show it in a distinct style (e.g., different sphere state or response label color) and keep the input focused/enabled immediately (no 2s delay)
3. `src/spaiOS/ui/components.py` — add a visual cue on `ResponseView` for "AI asking" vs "AI responding" (different label text or accent color)
4. Test: ask something ambiguous like "fix the bug" with no file open — AI should ask a clarifying question; answer it; AI should continue with context

**Notion task:** (create in Notion at session start — next card after Session 9 card)
**Task doc:** `docs/tasks/2026-04-27-m4-clarifying.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
