# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 4, Session 9

**Goal:** Upgrade Orchestrator to support conversation history (last 10 turns) and a structured, persistent system prompt — so follow-up questions work and the AI always knows the screen context.

**Steps (in order):**
1. `src/spaiOS/core/orchestrator.py` — add `self._history: list[dict]` (max 10 turns); `ask()` builds messages as `[system, *history, user]`, appends both user + assistant turns, trims to last 10 pairs
2. `src/spaiOS/ui/overlay.py` — wire a "clear history" reset when the overlay is hidden (Super+Space closes it), so next open starts fresh
3. Test: open VS Code with a Python file, ask "what does this code do?", then ask "any bugs?" — verify second answer references context from the first

**Notion task:** (create in Notion at session start — next card after 34e7600e54c781da8290e0c96c87ea64)
**Task doc:** `docs/tasks/2026-04-27-m4-history.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
