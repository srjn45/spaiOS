# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 2, Session 4

**Goal:** Neural Sphere QPainter widget with idle pulse and thinking/orbiting-nodes animation states.

**Steps (in order):**
1. Create `src/spaiOS/ui/neural_sphere.py` — `NeuralSphere(QWidget)` with `QPainter` `paintEvent`
2. Idle state: `QTimer` 50ms, scale oscillates 0.95→1.05, opacity 0.6→0.8
3. Thinking state: 8 satellite nodes at computed orbit positions, random flicker (`random.random() < 0.3`)
4. Responding state: nodes converge to center with lerp ease-in
5. Expose `set_state(state: str)` — trigger thinking via keyboard shortcut for testing
6. Wire `NeuralSphere` into `overlay.py`, replacing the Session 3 placeholder label
7. Verify all three animation states visually

**Session 5 continues with:** Text I/O + Ollama — QLineEdit, Orchestrator, QThread response flow

**Notion task:** 34e7600e54c781f3a741d961b4482155 (Milestone 2 task)
**Task doc:** `docs/tasks/2026-04-26-m2-the-overlay.md` (already exists)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
