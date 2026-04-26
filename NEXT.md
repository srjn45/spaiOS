# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 1, Session 2

**Goal:** Python project skeleton with working Ollama SDK smoke test.

**Steps (in order):**
1. Init project: `uv init spaiOS` (or configure existing dir) → set Python 3.12, configure `pyproject.toml`
2. Add dependencies: `uv add ollama pillow pyqt6 pyatspi pynput python-xlib`
3. Create `src/` layout: `ui/`, `core/`, `agents/`, `main.py` skeleton
4. Write smoke test: `ollama.chat('llama3.2:3b', messages=[{'role':'user','content':'say hi'}])` → print response
5. Write vision test: `scrot` screenshot → `PIL.Image.open()` → base64 → moondream → print description
6. Create `sandbox/` with 20+ messy test files for File Agent later
7. Verify: `uv run python src/main.py` exits cleanly

**Session 3 continues with:** Neural Sphere overlay widget (Phase 1, Milestone 2)

**Notion task:** [Milestone 1: Environment Setup](https://notion.so/34e7600e54c78140bdd8f41e364d4d1a)
**Task doc:** `docs/tasks/2026-04-26-m1-environment-setup.md`

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
