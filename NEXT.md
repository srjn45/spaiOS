# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 3, Session 7

**Goal:** Screen capture + vision model integration — capture the active window and feed it to `llava:7b` alongside the user prompt.

**Steps (in order):**
1. `src/spaiOS/core/screen_capture.py` — use `mss` (or `PIL` + `Xlib`) to capture the active window region; return a JPEG bytes buffer
2. `src/spaiOS/core/orchestrator.py` — add `AskWithVisionThread`: sends user message + base64-encoded image to `ollama.chat` with `llava:7b`
3. `src/spaiOS/ui/overlay.py` — add a camera-icon toggle button in the InputRow area; when active, capture is taken on submit
4. `src/spaiOS/ui/components.py` — extend `InputRow` with an optional camera toggle (`QPushButton` icon, no text)
5. Wire: toggle on → `AskWithVisionThread` used instead of `AskThread`; toggle off → text-only as before
6. Test: activate overlay, toggle camera, ask "what do you see?" — verify `llava:7b` response describes screen content

**Session 8 continues with:** AT-SPI context reader (active app name + selected text)

**Notion task:** (create new M3 task in Notion)
**Task doc:** `docs/tasks/2026-04-27-m3-vision.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
