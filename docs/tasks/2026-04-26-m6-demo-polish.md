# Task: Milestone 6 — The Demo + Polish

**Date:** 2026-04-26
**Phase:** Phase 1 — The Spark
**Sessions:** 16–19 (~8hrs)
**Notion task ID:** 34e7600e54c781c69f61ecc13d25c4ff

## What We're Building

The Phase 1 hero demo scenario end-to-end, then visual polish (drop shadow, gradient background, Markdown rendering in response area, smoother animation transitions), and finally packaging as a pip-installable `spaiOS` command with a first-run wizard.

## Approach

**Sessions 16–17 — Hero demo:**
1. Open VS Code with `demo_broken.py` containing a `ZeroDivisionError`
2. `Super+Space` → type "help with this error" → verify AI response identifies the error line and explains it
3. AI offers to fix → user says "yes" → corrected code displayed in overlay
4. Debug any gaps: AT-SPI not reading VS Code → try `XDG_SESSION_TYPE=x11`; moondream not seeing error → check base64 encoding
5. Record the full demo flow; document any workarounds needed

**Session 18 — Visual polish:**
6. Overlay drop shadow: `QGraphicsDropShadowEffect` on the overlay widget
7. Gradient background: `QPainter.fillRect` with `QLinearGradient` (dark navy → slightly lighter)
8. Animation: easing curves on sphere scale transitions using `QPropertyAnimation`
9. Markdown rendering in `QTextEdit`: parse `**bold**`, `` `code` ``, `- bullet` with `QTextDocument` rich text or custom renderer
10. Response text: Inter/system font, 14pt, 1.5 line spacing

**Session 19 — Packaging:**
11. `pyproject.toml`: `[project.scripts] spaiOS = "spaiOS.main:main"`
12. `src/main.py`: `main()` function as entry point
13. First-run wizard: on launch, check Ollama running (`GET /api/tags`); if not → show setup instructions; check models pulled; create `~/spaiOS-sandbox/` if missing
14. `spaiOS.desktop` file for GNOME launcher integration
15. `pip install .` smoke test from a clean venv

## Files Touched

- `src/main.py` — `main()` entry point, first-run wizard
- `src/ui/overlay.py` — drop shadow, gradient
- `src/ui/neural_sphere.py` — easing animation
- `src/ui/components.py` — Markdown response renderer
- `pyproject.toml` — entry point, package metadata
- `spaiOS.desktop` — GNOME launcher
- `sandbox/demo_broken.py` — broken Python file for hero demo

## Done When

1. Hero demo: VS Code with syntax error → "help with this error" → AI identifies the correct error line number
2. AI-offered fix is displayed in overlay as corrected code
3. Overlay has visible drop shadow and gradient background
4. Response area renders `**bold**`, `` `code` ``, and `- bullets` as rich text
5. `pip install .` succeeds; `spaiOS` command launches the overlay from a clean environment
6. First-run wizard shows actionable instructions if Ollama is not running
