# Task: Milestone 2 — The Overlay

**Date:** 2026-04-26
**Phase:** Phase 1 — The Spark
**Sessions:** 3–5 (~6hrs)
**Notion task ID:** 34e7600e54c781f3a741d961b4482155

## What We're Building

The PyQt6 Neural Sphere overlay: a frameless, always-on-top 480×420px window that activates on `Super+Space` and dismisses on `Esc`. Includes the custom `NeuralSphere` QPainter widget with idle pulse and thinking/orbiting-nodes animation states, QLineEdit for text input, QTextEdit for response display, and a wired-up Ollama call that plays the thinking animation while waiting.

## Approach

**Session 3 — Window shell:**
1. `src/ui/overlay.py`: PyQt6 window with `FramelessWindowHint | WindowStaysOnTopHint | Tool` flags, `WA_TranslucentBackground`
2. Center on primary screen, 480×420px
3. `src/core/hotkey.py`: `pynput.keyboard.GlobalHotKeys` in background thread listening for `<super>+space`
4. Hotkey fires a signal → shows overlay; `Esc` key event → hides overlay
5. Verify: window appears, dismisses, no crash on repeat

**Session 4 — Neural Sphere animation:**
6. `src/ui/neural_sphere.py`: `NeuralSphere(QWidget)` with `QPainter` `paintEvent`
7. Idle state: `QTimer` 50ms, scale oscillates 0.95→1.05, opacity 0.6→0.8
8. Thinking state: 8 satellite nodes at computed orbit positions, random flicker via `random.random() < 0.3`
9. Responding state: nodes converge to center with ease-in (lerp toward center)
10. Expose `set_state(state: str)` method; trigger thinking via keyboard shortcut for testing

**Session 5 — Text I/O + Ollama:**
11. `src/ui/components.py`: `QLineEdit` ("Ask anything…") + `QPushButton` ("↵")
12. `src/core/orchestrator.py` stub: takes user message, calls `ollama.chat`, returns response
13. On Enter: emit signal → `Orchestrator.ask()` in `QThread` → `set_state('thinking')` → on result → `set_state('idle')` → display response in `QTextEdit`
14. Handle `Esc` while thinking: cancel thread, return to idle

## Files Touched

- `src/ui/overlay.py` — main window
- `src/ui/neural_sphere.py` — QPainter widget
- `src/ui/components.py` — input/response widgets
- `src/core/hotkey.py` — global Super+Space listener
- `src/core/orchestrator.py` — stub Ollama caller
- `src/main.py` — init Qt app, start hotkey thread, exec loop

## Done When

1. `Super+Space` shows overlay in under 500ms
2. `Esc` dismisses overlay cleanly; immediate re-open works
3. `NeuralSphere` idle state: circle pulses scale 0.95→1.05 visibly at 50ms tick
4. `NeuralSphere` thinking state: 8 nodes orbit with random flicker
5. Type a prompt + Enter → thinking animation plays → Ollama `llama3.2:3b` response appears in overlay
