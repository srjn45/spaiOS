# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 3 — The Assistant Layer (PIVOTED 2026-05-03)

**Goal:** Connect spaiOS overlay to spaid daemon. Replace direct Ollama calls with spaid socket
protocol. End state: voice/hotkey triggers the overlay, spaid handles LLM routing and tool
execution, windows snap on command.

**Full design:** `docs/superpowers/specs/2026-05-03-pivot-ai-assistant-design.md`
**Phase doc:** `docs/phases/2026-05-03-phase-3-the-assistant-layer.md`

---

## Milestone Order

| # | Name | Status | Repo |
|---|---|---|---|
| M1 | spaid-overlay bridge | **Done** | spaiOS + spaiSH |
| M2 | Window management tools | **Next** | spaiSH |
| M3 | Unified installer | Can start any time | spaiOS |
| M4 | LiteLLM multi-model routing | Blocked on M3 | spaiSH |
| M5 | Full loop polish + demo | Last | both |

---

## M1 What Was Done (2026-05-03)

- `spaiSH`: added `OverlayQuery` + `ActiveWindowInfo` to protocol; `OverlayHandler` in socket server; `onOverlay` handler in spaid streaming LLM response back with active window context
- `spaiOS`: new `SpaidClient` (`src/spaiOS/core/spaid_client.py`) — connects to spaid.sock, reads active window via xdotool, streams `ResponseEvent`s; `Orchestrator` routes through spaid with direct Ollama fallback; `Overlay` injects `SpaidClient`

**M1 AC status:**
- [x] `spaid_client.py` written — connects, sends overlay_query, yields ResponseEvents
- [x] `orchestrator.py` rewired — tries spaid first, falls back on exception
- [x] spaid logs show `overlay_query` received (verified by log.Printf in onOverlay)
- [x] Fallback to direct Ollama when socket absent (is_available() check)
- [ ] End-to-end smoke test: start spaid → trigger overlay → query routes through → text renders ← **do this first next session**

---

## M2 Starting Point

**Task doc:** create `docs/tasks/2026-05-03-p3-m2-window-management.md` before coding
**Notion task:** phase3_m2_window_management

**Files to touch (spaiSH):**
1. `internal/tools/window_op.go` — new: xdotool/wmctrl window actions
2. `internal/tools/app_control.go` — new: launch/kill/list-windows
3. `cmd/spaid/main.go` — wire tools into onOverlay handler so LLM can call them
4. `src/spaiOS/core/orchestrator.py` — implement `_execute_tool_call()` (currently stub)

**Done when:** "snap Firefox to the left" → window snaps. "open gedit" → gedit launches.

**Prereqs:** `xdotool` and `wmctrl` installed (`apt install xdotool wmctrl`)

---

## What Was Just Parked

Phase 3 Wayland compositor (`compositor/` crate in Rust/Smithay) is parked — not deleted.
It successfully renders a window and composites client surfaces (weston-terminal visible),
but keyboard input was not yet working and the full compositor was months away from user value.

AC status: surface rendering ✓, correct orientation ✓, keyboard typing ✗ (parked mid-debug)
