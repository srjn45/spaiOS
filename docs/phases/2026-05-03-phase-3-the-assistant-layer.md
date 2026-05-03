# Phase 3: The Assistant Layer

**Status:** Active — started 2026-05-03
**Replaces:** 2026-04-26-phase-3-the-shell.md (Wayland compositor — parked)
**Target:** ~10 sessions × 2hrs
**Output:** spaiOS + spaiSH integrated; voice/hotkey controls windows, launches apps, runs commands through spaid on any X11 Linux desktop

---

## Goal

Make spaiOS genuinely useful on any Linux machine running X11 — today, without building a new OS. The user presses `Super+Space` (or says a wake word), describes what they want, and the AI acts: snaps windows, opens apps, runs shell commands.

**Showcase scenario:** User is on Ubuntu GNOME. They say "hey spai". Neural sphere appears. They say "put Firefox on the left and VS Code on the right". Both windows snap to halves of the screen. No mouse required.

---

## What Changed from the Original Phase 3

The original Phase 3 targeted a custom Wayland compositor in Rust (Smithay). After bootstrapping it, it became clear this would take months before delivering user value.

Instead: **extend what already works**. spaiOS (Python overlay) and spaiSH (Go daemon) are both functional. Phase 3 connects them, adds window management, and adds a unified installer.

Full rationale: `docs/superpowers/specs/2026-05-03-pivot-ai-assistant-design.md`

---

## Architecture Summary

```
Voice/Hotkey
    ↓
spaiOS overlay (PyQt6)
    ↓ Unix socket
spaid daemon (Go)
    ↓
LLM → tool calls
    ↓
window_op / app_control / shell_exec
```

spaiOS owns: wake detection, transcription, hotkey, screen capture, overlay UI rendering.
spaid owns: LLM routing, tool execution, permission tiers, session context.

---

## Milestones

### M1: spaid-Overlay Bridge (~2 sessions)

Connect spaiOS to spaid via Unix socket. Replace direct Ollama call in orchestrator.

**Files touched:**
- `src/spaiOS/core/spaid_client.py` (new)
- `src/spaiOS/core/orchestrator.py` (rewire)

**Done when:** Overlay activates → query goes to spaid → streamed text response renders in neural sphere. Direct Ollama fallback works if spaid unreachable.

---

### M2: Window Management (~2 sessions)

Add `window_op` and `app_control` tools to spaid. Requires `xdotool` + `wmctrl`.

**Files touched (spaiSH):**
- `internal/tools/window_op.go` (new)
- `internal/tools/app_control.go` (new)
- `internal/protocol/types.go` (add overlay_query message type)
- `cmd/spaid/main.go` (wire new tools into request handler)

**Done when:** "snap Firefox to the left" → window snaps. "open gedit" → gedit launches. "close this window" → active window closes.

---

### M3: Unified Installer (~1 session)

Single script to install/uninstall/reinstall both spaiSH and spaiOS from local source.

**Files touched (spaiOS):**
- `scripts/spai-install.sh` (new)

**Done when:** `./scripts/spai-install.sh reinstall` builds Go binaries, installs Python package, registers systemd service + autostart entry, completes in < 2 minutes.

---

### M4: LiteLLM Multi-Model Routing (~2 sessions)

Replace spaid's single-provider router with LiteLLM. Priority queue: Claude → GPT-4o-mini → local Ollama. Auto-fallback on rate limit or offline.

**Files touched (spaiSH):**
- `internal/llm/litellm.go` (new or replace existing router)
- `config/spaid.toml` (new `[models]` section)

**Done when:** With `ANTHROPIC_API_KEY` set, queries route to Claude. Kill internet → falls back to Ollama automatically. Config priority list respected.

---

### M5: Full Loop Polish (~2 sessions)

End-to-end demo hardening. Fix rough edges found in M1–M4. Update docs.

**Done when (Phase 3 acceptance criteria):**
1. `Super+Space` → "snap Firefox to the left" → Firefox snaps
2. Wake word → "open terminal" → terminal launches
3. `spai explain why my build failed` still works (no regression in spaiSH)
4. Disconnect internet → falls back to local Ollama
5. `spai-install.sh reinstall` completes cleanly in < 2 minutes

---

## Key Dependencies

| Tool | Purpose | Install |
|---|---|---|
| `xdotool` | Window operations, active window query | `apt install xdotool` |
| `wmctrl` | Maximize/snap/list windows | `apt install wmctrl` |
| `xdotool getdisplaygeometry` | Screen dimensions for snap math | (comes with xdotool) |
| LiteLLM | Multi-model routing layer | `pip install litellm` |

---

## Out of Scope for Phase 3

- Wayland window management
- Custom compositor / bootable ISO
- eBPF / kernel integration
- Generative UI blueprint cards
- Screenshot analysis (visual context for LLM)

These remain on the long-term roadmap but are not blockers for a working AI assistant.
