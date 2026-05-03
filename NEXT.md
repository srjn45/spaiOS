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
| M1 | spaid-overlay bridge | **Next** | spaiOS |
| M2 | Window management tools | Blocked on M1 | spaiSH |
| M3 | Unified installer | Can start any time | spaiOS |
| M4 | LiteLLM multi-model routing | Blocked on M3 | spaiSH |
| M5 | Full loop polish + demo | Last | both |

---

## M1 Starting Point

**Task doc:** `docs/tasks/2026-05-03-p3-m1-spaid-client-overlay.md`
**Notion task:** phase3_m1_spaid_overlay_bridge

**Steps:**
1. Extend spaiSH socket protocol — add `OverlayQuery` + `OverlayResponse` types
2. Wire `overlay_query` handler in `cmd/spaid/main.go`
3. Write `src/spaiOS/core/spaid_client.py` with socket connect + streaming query
4. Rewire `src/spaiOS/core/orchestrator.py` to call spaid_client
5. Test: trigger overlay → query spaid → text streams into neural sphere

**Repos needed:**
- `/home/srajan/Development/spaiOS` (this repo)
- `/home/srajan/Development/spaiSH` (Go daemon)

---

## What Was Just Parked

Phase 3 Wayland compositor (`compositor/` crate in Rust/Smithay) is parked — not deleted.
It successfully renders a window and composites client surfaces (weston-terminal visible),
but keyboard input was not yet working and the full compositor was months away from user value.

AC status: surface rendering ✓, correct orientation ✓, keyboard typing ✗ (parked mid-debug)
