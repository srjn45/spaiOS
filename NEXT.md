# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 2, Session 3

**Goal:** Neural Sphere overlay widget — a transparent, always-on-top PyQt6 window with a pulsing sphere animation.

**Steps (in order):**
1. Create `src/spaiOS/ui/overlay.py` — `QMainWindow` subclass, frameless, transparent, always-on-top
2. Draw the Neural Sphere: `QGraphicsView` + `QGraphicsEllipseItem` or raw `QPainter` on canvas
3. Idle pulse animation: gentle scale/opacity oscillation using `QPropertyAnimation` or `QTimer`
4. Position: bottom-right corner of primary screen, draggable
5. Global hotkey: `Ctrl+Space` to show/hide overlay using `pynput`
6. Verify: overlay appears, pulses, and can be toggled with hotkey

**Session 4 continues with:** Screen capture pipeline — periodic screenshot → moondream description → context buffer

**Notion task:** Check Notion task board for Milestone 2 task ID
**Task doc:** `docs/tasks/2026-04-26-m2-neural-sphere.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
