# spaiOS Pivot — AI Assistant for Linux: Design Spec

**Date:** 2026-05-03 | **Version:** 1.0 | **Author:** Srajan Pathak
**Supersedes:** Original Phase 3 (custom Wayland compositor)

---

## Why We Pivoted

The original Phase 3 goal was a custom Wayland compositor in Rust. After bootstrapping it with Smithay 0.7, the estimate to reach "weston-terminal accepts keyboard input" was already several sessions deep, and a full compositor with GPU rendering, XWayland, and a bootable Alpine ISO would have taken months more.

Meanwhile, **two complementary projects already exist and work**:

- **spaiOS** — PyQt6 overlay with neural sphere, voice wake (Whisper), hotkey, screen capture, AT-SPI, LLM integration, file/chrome/code agents.
- **spaiSH** — Go daemon (`spaid`) with Unix socket IPC, permission tiers, session context, model routing (cloud + local Ollama), CLI (`spai`), interactive shell (`spaish`).

The pivot reframes the goal: instead of building a new OS, build **the best AI assistant layer that works on top of any existing Linux desktop**. Same end value (AI-native computing), much faster time to something genuinely useful and shippable.

---

## New One-Line

> spaiOS is an AI assistant for Linux that works on any distro and any desktop — triggered by voice or hotkey, sees what you see, controls your windows, and runs commands with your permission.

---

## Target Platform

- **Display:** X11 sessions (covers Ubuntu, Fedora, Mint, Manjaro on GNOME/KDE/XFCE)
- **Wayland:** Deferred — no universal window-control protocol exists yet
- **Distros:** Any with systemd + Python 3.11+ + Go 1.21+
- **Desktop environments:** GNOME, KDE, XFCE (anything running X11)

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              spaiOS (Python)                 │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │voice wake│  │ hotkey   │  │screen cap │ │
│  │Whisper   │  │Super+Spc │  │AT-SPI ctx │ │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │
│       └─────────────▼───────────────┘        │
│                 ┌──────────┐                  │
│                 │ overlay  │ ← neural sphere  │
│                 │   UI     │   text rendering │
│                 └────┬─────┘                  │
│                      │                        │
│              ┌───────▼───────┐               │
│              │ spaid_client  │ (NEW module)   │
│              │ Unix socket   │               │
│              └───────┬───────┘               │
└──────────────────────┼──────────────────────┘
                       │ ~/.local/share/spaish/spaid.sock
┌──────────────────────┼──────────────────────┐
│              spaid (Go)                      │
│                                              │
│  ┌────────────────────▼──────────────────┐  │
│  │           Request Router              │  │
│  │  shell_event │ overlay_query (NEW)    │  │
│  └──────┬───────────────────────────────┘  │
│         │                                   │
│  ┌──────▼────────┐  ┌──────────────────┐  │
│  │  LLM Router   │  │   Tool Engine    │  │
│  │  (existing)   │  │                  │  │
│  │               │  │ shell_exec ✓     │  │
│  │               │  │ window_op  (NEW) │  │
│  │               │  │ app_control(NEW) │  │
│  └───────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────┘
```

**What stays unchanged in spaiOS:** wake detection, Whisper transcription, hotkey, neural sphere animation, screen capture, AT-SPI context, all existing agents.

**What stays unchanged in spaiSH:** permission tiers, session context, model routing, `spai` CLI, `spaish` interactive shell.

---

## Protocol: overlay_query

A new message type added to spaid's existing JSON-over-Unix-socket protocol. Non-breaking — existing `spai` CLI keeps using `shell_event`.

### Request (spaiOS → spaid)

```json
{
  "type": "overlay_query",
  "query": "snap firefox to the left half",
  "session_id": "overlay-default",
  "active_window": {
    "title": "Firefox",
    "win_id": "0x04200003",
    "pid": 12345,
    "geometry": { "x": 0, "y": 0, "w": 1280, "h": 800 }
  }
}
```

### Response stream (spaid → spaiOS)

```json
{ "type": "text",      "text": "Snapping Firefox to the left half." }
{ "type": "tool_call", "tool": "window_op", "params": { "win_id": "0x04200003", "action": "snap_left" } }
{ "type": "done" }
```

- `text` events: rendered in overlay as AI speech
- `tool_call` events: executed by spaiOS locally (xdotool/wmctrl run on the user's machine)
- `error` events: shown in overlay with red indicator

---

## New Tools in spaid

Both tools live in a new `internal/tools/` package in spaiSH. Dependencies: `xdotool`, `wmctrl` (installed by the unified installer).

### window_op

Wraps `xdotool` and `wmctrl` subprocess calls.

| Action | Command |
|---|---|
| `minimize` | `xdotool windowminimize <id>` |
| `maximize` | `wmctrl -ir <id> -b add,maximized_vert,maximized_horz` |
| `fullscreen` | `wmctrl -ir <id> -b add,fullscreen` |
| `restore` | `wmctrl -ir <id> -b remove,maximized_vert,maximized_horz,fullscreen` |
| `focus` | `xdotool windowactivate <id>` |
| `close` | `xdotool windowclose <id>` |
| `snap_left` | `wmctrl -ir <id> -e 0,0,0,{W/2},{H}` |
| `snap_right` | `wmctrl -ir <id> -e 0,{W/2},0,{W/2},{H}` |
| `snap_top` | `wmctrl -ir <id> -e 0,0,0,{W},{H/2}` |
| `snap_bottom` | `wmctrl -ir <id> -e 0,0,{H/2},{W},{H/2}` |

Screen dimensions fetched once per request via `xdotool getdisplaygeometry`.

### app_control

| Action | Implementation |
|---|---|
| `launch` | `exec.Command(app)` detached from spaid process tree |
| `kill` | `wmctrl -c <title>` graceful, fallback `pkill <name>` |
| `list_windows` | `wmctrl -l` → returns title + ID list injected into LLM context |

---

## spaiOS Changes

**Minimal surface area** — only two files change in the Python codebase:

### New: `src/spaiOS/core/spaid_client.py`

```python
class SpaidClient:
    def connect(self) -> None               # connect to spaid.sock, retry on failure
    def query(self,
              text: str,
              active_window: dict
             ) -> Iterator[ResponseEvent]   # streams text/tool_call/done events
    def get_active_window(self) -> dict     # xdotool getactivewindow + getwindowname
    def close(self) -> None
```

Auto-reconnects if spaid restarts. Falls back to direct Ollama path if socket unavailable (dev convenience).

### Modified: `src/spaiOS/core/orchestrator.py`

Replace the direct `llm.py` call with `SpaidClient.query(...)`. The overlay rendering loop stays identical — it already processes streamed text tokens. Tool call events are routed to a new `execute_tool_call(event)` dispatcher that calls `xdotool`/`wmctrl` locally.

---

## Multi-Model Routing (Phase 3 M4 — spaiSH)

spaid's existing model router is replaced with **LiteLLM** as the routing layer.

Config in `~/.config/spaish/spaid.toml`:

```toml
[models]
priority = ["claude-3-5-haiku", "gpt-4o-mini", "ollama/qwen2.5-coder"]

[models.claude-3-5-haiku]
provider = "anthropic"
api_key_env = "ANTHROPIC_API_KEY"
context_limit = 200000

[models.gpt-4o-mini]
provider = "openai"
api_key_env = "OPENAI_API_KEY"
context_limit = 128000

[models.ollama/qwen2.5-coder]
provider = "ollama"
endpoint = "http://localhost:11434"
offline_only = false          # set true to use only when no internet
```

Routing logic: try models in priority order. Move to next on: rate limit, API error, no internet. Always fall back to local Ollama if all cloud models fail.

---

## Unified Installer

Single script: `scripts/spai-install.sh` at spaiOS repo root.

```bash
spai-install.sh [install|uninstall|reinstall]
```

### Install sequence

1. Check deps: `go ≥1.21`, `python3`, `uv`, `xdotool`, `wmctrl`, `systemd`
2. Build spaiSH binaries from `$SPAISH_DIR`: `spaid`, `spai`, `spaish` → `~/.local/bin/`
3. Install spaiOS via `uv pip install -e $SPAIOS_DIR`
4. Write `~/.config/systemd/user/spaid.service`
5. Write `~/.config/autostart/spaios.desktop`
6. Create `~/.config/spaish/spaid.toml` if absent
7. `systemctl --user daemon-reload && systemctl --user enable --now spaid`
8. Print: `✓ spaiOS ready. Press Super+Space or say your wake word.`

### Uninstall sequence

1. `systemctl --user stop spaid && systemctl --user disable spaid`
2. Remove `~/.local/bin/{spaid,spai,spaish}`
3. Remove `~/.config/autostart/spaios.desktop`
4. Remove `~/.config/systemd/user/spaid.service`
5. Leave `~/.config/spaish/spaid.toml` + session data intact (user data)

### Reinstall

`uninstall` → `install` (rebuilds all binaries from latest source).

---

## Milestone Roadmap (Phase 3)

| M# | Name | Key deliverable | Repo |
|---|---|---|---|
| M1 | spaid-overlay bridge | spaid_client.py + orchestrator rewire | spaiOS |
| M2 | Window management | window_op + app_control tools in spaid | spaiSH |
| M3 | Unified installer | spai-install.sh install/uninstall/reinstall | spaiOS |
| M4 | LiteLLM routing | Multi-model priority queue replacing direct Ollama | spaiSH |
| M5 | Full loop polish | Demo: voice → window snap, app launch, shell cmd | both |

### Phase 3 acceptance criteria (done when all pass)

1. Press `Super+Space` → overlay opens → say "snap Firefox to the left" → Firefox snaps
2. Say wake word → overlay activates → say "open terminal" → terminal launches
3. `spai explain why my build failed` in any terminal still works (no regression)
4. Disconnect internet → assistant falls back to local Ollama automatically
5. `spai-install.sh reinstall` completes cleanly from fresh state in < 2 minutes

---

## Deferred (not Phase 3)

- Wayland window management (no universal protocol yet)
- Custom compositor (original Phase 3 — parked, not deleted)
- Alpine Linux ISO / bootable distro
- eBPF kernel integration
- Generative UI / blueprint cards
