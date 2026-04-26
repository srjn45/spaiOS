# Task: Session 6 — Polish Pass

**Date:** 2026-04-27
**Phase:** Phase 1 — The Spark
**Session goal:** Introduce design tokens, font consistency, opacity fade-in, sphere color tweens, and tighter layout.
**Notion task ID:** 34e7600e54c781f3a741d961b4482155

## What We're Building

Visual polish for the existing overlay: a shared token module, consistent "Ubuntu Sans" font across all text widgets, a smooth windowOpacity fade-in when the overlay appears, and a glow color tween on the NeuralSphere that transitions between idle/thinking/responding states.

## Approach

1. `src/spaiOS/ui/tokens.py` — color constants + font family/sizes
2. `components.py` — apply font tokens to InputRow (QLineEdit, QPushButton) and ResponseView (QTextEdit)
3. `overlay.py` — override `show()` with QPropertyAnimation on windowOpacity (0→1, 200ms)
4. `neural_sphere.py` — lerp glow color between idle/thinking/responding on each tick
5. `overlay.py` + `components.py` — tighten layout margins and spacing for 540px balance

## Files Touched

- `src/spaiOS/ui/tokens.py` — NEW: design token constants
- `src/spaiOS/ui/components.py` — apply font tokens
- `src/spaiOS/ui/overlay.py` — opacity fade-in animation
- `src/spaiOS/ui/neural_sphere.py` — glow color tween

## Done When

1. `tokens.py` exists with FONT_FAMILY, font size constants, and color palette
2. InputRow and ResponseView render "Ubuntu Sans" at defined sizes
3. Overlay fades in over ~200ms (not a hard snap) on every show
4. NeuralSphere glow smoothly shifts color between states (purple idle → blue thinking → green responding)
5. Layout looks balanced at 540px — no cramped or over-spaced sections
