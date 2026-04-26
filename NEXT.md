# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 2, Session 5

**Goal:** Text I/O + Ollama integration — QLineEdit input, Orchestrator, QThread response flow.

**Steps (in order):**
1. `src/spaiOS/ui/components.py` — `QLineEdit` ("Ask anything…") + `QPushButton` ("↵")
2. Wire input row into `overlay.py` below the NeuralSphere
3. `src/spaiOS/core/orchestrator.py` — `Orchestrator` class with `ask(prompt: str) -> str` calling `ollama.chat` with `llama3.2:3b`
4. `QThread` subclass `AskThread` — emits `result(str)` and `error(str)` signals
5. On Enter: emit signal → start `AskThread` → `sphere.set_state("thinking")`
6. On `AskThread.result`: `sphere.set_state("responding")` → display text in `QTextEdit`
7. On `Esc` while thinking: stop thread, return to idle
8. Check Ollama is running before call; show friendly error in overlay if not

**Session 6 continues with:** Polish pass — font, spacing, color tokens, opacity transitions

**Notion task:** 34e7600e54c781f3a741d961b4482155 (Milestone 2 task)
**Task doc:** `docs/tasks/2026-04-26-m2-the-overlay.md` (already exists)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
