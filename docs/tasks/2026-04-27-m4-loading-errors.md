# Task: Loading States and Error Handling

**Date:** 2026-04-27
**Phase:** Phase 1 — Milestone 4, Session 11
**Session goal:** Improve Ollama error messages and add long-response truncation with "show more" to the overlay.
**Notion task ID:** (add when created in Notion)

## What We're Building

Two improvements to make the overlay more production-quality:
1. **Richer error handling** — specific, actionable messages for each Ollama failure mode (server down, model missing, timeout).
2. **Long-response truncation** — responses over ~380 chars are clipped with a "Show more ↓" toggle so the overlay stays compact.

## Approach

1. Improve `_emit_ollama_error` in `orchestrator.py` — detect model-not-found and timeout patterns in addition to connection refused.
2. Refactor `ResponseView` in `components.py` from a `QTextEdit` subclass to a `QWidget` container holding a `QTextEdit` + optional "Show more" `QPushButton`.
3. Implement truncation: if `len(text) > _TRUNCATE_CHARS` show first 380 chars + "…", reveal button. Button toggles between full/truncated view.
4. `show_error()` skips truncation (errors are short, every word matters).
5. Verify all call-sites in `overlay.py` still work (same public API).

## Files Touched

- `src/spaiOS/core/orchestrator.py` — `_emit_ollama_error` improvements
- `src/spaiOS/ui/components.py` — `ResponseView` refactor + truncation

## Done When

- Sending a prompt while Ollama is down shows "Ollama is not running. Start it with: ollama serve"
- Pulling a non-existent model name in `_MODEL` shows "Model not found. Run: ollama pull …"
- A response longer than 380 chars is truncated with "Show more ↓" visible
- Clicking "Show more ↓" expands to full text, button changes to "Show less ↑"
- Clicking again collapses back
- Short responses show no button at all
