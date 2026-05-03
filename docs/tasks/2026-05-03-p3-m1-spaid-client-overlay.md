# Task: P3-M1 — spaid-Overlay Bridge

**Date:** 2026-05-03
**Phase:** Phase 3 — The Assistant Layer
**Session goal:** Connect spaiOS overlay to spaid daemon via Unix socket. Replace direct Ollama call.
**Notion task ID:** phase3_m1_spaid_overlay_bridge

## What We're Building

A new `SpaidClient` module in spaiOS that speaks the spaid socket protocol. The orchestrator stops calling Ollama directly and instead routes all queries through spaid, which handles LLM routing, context, and tool execution. The overlay UI is unchanged — it just renders whatever spaid streams back.

## Approach

1. Write `src/spaiOS/core/spaid_client.py`:
   - Connect to `~/.local/share/spaish/spaid.sock`
   - `get_active_window()` using `xdotool getactivewindow` + `xdotool getwindowname`
   - `query(text, active_window)` sends `overlay_query` JSON, yields `ResponseEvent` objects
   - Auto-reconnect on socket disconnect
2. Extend spaid socket protocol (`internal/protocol/types.go` in spaiSH):
   - Add `OverlayQuery` request struct
   - Add `OverlayResponse` response struct (`type: text|tool_call|done|error`)
3. Wire `overlay_query` into spaid's request router (`cmd/spaid/main.go`)
4. Modify `src/spaiOS/core/orchestrator.py`:
   - Inject `SpaidClient` at construction
   - Route queries through `spaid_client.query()` instead of `llm.py`
   - Handle `tool_call` events: dispatch to `execute_tool_call()` (stub for now)
   - Fallback: if socket unavailable, use existing Ollama path
5. Test: overlay activates → query sent → streamed text renders in sphere

## Files Touched

- `src/spaiOS/core/spaid_client.py` — new
- `src/spaiOS/core/orchestrator.py` — rewire LLM call
- `spaiSH/internal/protocol/types.go` — add overlay message types
- `spaiSH/cmd/spaid/main.go` — handle overlay_query

## Done When

- [ ] Overlay query goes to spaid, streams text back, renders in neural sphere
- [ ] `spaid` logs show `overlay_query` received with active window context
- [ ] If spaid not running, falls back to direct Ollama with a warning log
- [ ] No regression: existing `spai` CLI still works
