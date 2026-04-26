# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 3, Session 8

**Goal:** AT-SPI context reader — extract active app name, window title, and selected/visible text from the focused window to inject into the system prompt.

**Steps (in order):**
1. `src/spaiOS/core/context.py` — new file; `get_window_info() -> dict` via `xdotool getactivewindow getwindowname`; `get_atspi_text(max_chars: int = 2000) -> list[str]` via `pyatspi`; `capture() -> dict` combining all fields
2. `src/spaiOS/core/orchestrator.py` — `Orchestrator.ask()` calls `context.capture()` and prepends a system prompt with `app_name`, `window_title`, `visible_text`
3. Test: with a text editor open, ask "what text is on screen?" — verify the response references actual content

**Notion task:** 34e7600e54c781da8290e0c96c87ea64
**Task doc:** `docs/tasks/2026-04-27-m3-atspi.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
