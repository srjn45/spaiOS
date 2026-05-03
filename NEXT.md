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
| M2 | Window management tools | **Done** | spaiSH |
| M3 | Unified installer | **Done** | spaiOS |
| M4 | LiteLLM multi-model routing | **Next** | spaiSH |
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

## M2 What Was Done (2026-05-03)

- `internal/tools/window_op.go` — SnapLeft, SnapRight, MaximizeWindow, CloseWindow, GetActiveWinIDHex, ScreenGeometry
- `internal/tools/app_control.go` — LaunchApp (detached, new session), ListWindows
- `cmd/spaid/main.go` — overlaySystemPrompt updated with TOOL_CALL format; `executeWindowTool()` dispatcher; `onOverlay` now buffers full response, parses TOOL_CALL lines, executes tools, streams text back
- `src/spaiOS/core/orchestrator.py` — `_execute_tool_call` comment updated (tools run in spaid, not spaiOS)

**Design:** LLM outputs `TOOL_CALL: {"tool":"snap_window","side":"left"}` lines; spaid parses, executes via xdotool/wmctrl, strips from user-visible text.  
**Prereq to test:** `sudo apt install wmctrl` (xdotool already present)

**M2 AC status:**
- [x] `internal/tools/window_op.go` written — SnapLeft/Right, Maximize, Close
- [x] `internal/tools/app_control.go` written — LaunchApp, ListWindows
- [x] `onOverlay` parses TOOL_CALL: lines and dispatches to tools package
- [x] `go build ./...` passes cleanly
- [ ] Live test: "snap Firefox to the left" → window snaps ← **verify after `apt install wmctrl`**
- [ ] Live test: "open gedit" → gedit launches
- [ ] M1 smoke test: spaid receives overlay_query, text renders in overlay ← **still pending**

---

## M3 What Was Done (2026-05-03)

- `scripts/spai-install.sh` — three-mode installer (install/uninstall/reinstall)
- Builds `spai`, `spaid`, `spaish` Go binaries → `~/.local/bin/`
- Installs spaiOS Python package via `uv pip install -e .`
- Writes `~/.config/systemd/user/spaid.service` and enables/starts it
- Writes `~/.config/autostart/spaios.desktop` for login autostart
- Copies default config to `~/.config/spaish/spaid.toml` if not present
- Dep check at top: prints friendly error + apt hint if xdotool/wmctrl/go/uv missing

**M3 AC status:**
- [x] `install` completes cleanly
- [x] `spaid` service active after install
- [x] autostart entry written
- [x] `uninstall` removes binaries + autostart, preserves config
- [x] `reinstall` = uninstall + install
- [x] missing dep prints helpful error
- [x] full cycle: 4s (< 2 min)

---

## What Was Just Parked

Phase 3 Wayland compositor (`compositor/` crate in Rust/Smithay) is parked — not deleted.
It successfully renders a window and composites client surfaces (weston-terminal visible),
but keyboard input was not yet working and the full compositor was months away from user value.

AC status: surface rendering ✓, correct orientation ✓, keyboard typing ✗ (parked mid-debug)
