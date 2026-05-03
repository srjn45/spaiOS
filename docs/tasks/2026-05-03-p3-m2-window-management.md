# Task: P3-M2 — Window Management Tools

**Date:** 2026-05-03
**Phase:** Phase 3 — The Assistant Layer
**Session goal:** Add window_op and app_control tools to spaid. X11 only via xdotool + wmctrl.
**Notion task ID:** phase3_m2_window_management

## What We're Building

Two new tools in spaid's tool engine that give the AI the ability to control windows and applications on the user's X11 desktop.

`window_op` — minimize, maximize, fullscreen, restore, focus, close, snap to halves
`app_control` — launch app, kill app, list open windows

## Approach

1. Create `internal/tools/window_op.go` in spaiSH:
   - Helper: `getDisplayGeometry()` via `xdotool getdisplaygeometry`
   - Helper: `runXdotool(args...)` and `runWmctrl(args...)`
   - Implement all actions from the design spec
   - Snap math: `snap_left` = geometry `0,0,{W/2},{H}`, `snap_right` = `{W/2},0,{W/2},{H}`, etc.
2. Create `internal/tools/app_control.go` in spaiSH:
   - `launch`: `exec.Command` detached (new process group, not child of spaid)
   - `kill`: `wmctrl -c <title>` first, fallback `pkill <name>`
   - `list_windows`: parse `wmctrl -l` output, return title+ID list
3. Register tools in spaid's tool registry
4. Write tool descriptions for LLM system prompt so AI knows when to call them
5. Handle `tool_call` events in spaiOS `execute_tool_call()`:
   - `window_op` and `app_control` execute locally in spaiOS (xdotool/wmctrl on user's machine)
   - Send `tool_result` back to spaid if needed for multi-turn

## Files Touched (spaiSH)

- `internal/tools/window_op.go` — new
- `internal/tools/app_control.go` — new
- `internal/tools/registry.go` — register new tools
- `cmd/spaid/main.go` — include tools in LLM system prompt

## Files Touched (spaiOS)

- `src/spaiOS/core/spaid_client.py` — add `execute_tool_call()` dispatcher

## Done When

- [ ] "snap Firefox to the left" → Firefox moves to left half of screen
- [ ] "maximize VS Code" → VS Code maximizes
- [ ] "open terminal" → terminal emulator launches
- [ ] "close this window" → active window closes
- [ ] "minimize all windows" → all windows minimized (wmctrl -k on)
- [ ] Unknown app names fail gracefully with user-visible error
