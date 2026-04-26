# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 2, Session 6

**Goal:** Polish pass — font, spacing, color tokens, opacity transitions on overlay.

**Steps (in order):**
1. Define a color/font token module (`src/spaiOS/ui/tokens.py`) — shared palette constants
2. Apply consistent font (Inter or system sans-serif, size scale) across InputRow + ResponseView
3. Smooth opacity fade-in when overlay shows (`QPropertyAnimation` on `windowOpacity`)
4. Smooth idle→thinking→responding visual transitions (sphere glow color tween)
5. Tighten layout spacing and padding — ensure 540px height feels balanced
6. Test full flow: Super+Cmd+Space → type → Enter → thinking → response → Esc

**Session 7 continues with:** Screen capture + vision model integration

**Notion task:** 34e7600e54c781f3a741d961b4482155 (Milestone 2 task)
**Task doc:** `docs/tasks/2026-04-26-m2-the-overlay.md`

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
