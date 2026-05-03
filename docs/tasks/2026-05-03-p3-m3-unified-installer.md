# Task: P3-M3 — Unified Installer

**Date:** 2026-05-03
**Phase:** Phase 3 — The Assistant Layer
**Session goal:** Single script to install/uninstall/reinstall spaiSH + spaiOS from local source.
**Notion task ID:** phase3_m3_unified_installer

## What We're Building

`scripts/spai-install.sh` — a single Bash script that manages both spaiSH (Go binaries) and spaiOS (Python package) with three sub-commands: `install`, `uninstall`, `reinstall`.

Designed for local dev use first (builds from source paths), extensible later to download releases.

## Approach

1. Write `scripts/spai-install.sh` with three modes:
   - `install`: build Go binaries, install Python pkg, write systemd service + autostart
   - `uninstall`: stop/disable service, remove binaries, remove autostart entry
   - `reinstall`: uninstall then install
2. Dependency check at top: `go`, `python3`, `uv`, `xdotool`, `wmctrl`, `systemctl`
   - Print clear error and exit if any missing
   - Offer install hint: `sudo apt install xdotool wmctrl`
3. Go build: `cd $SPAISH_DIR && go build -o ~/.local/bin/spaid ./cmd/spaid` etc.
4. Python install: `cd $SPAIOS_DIR && uv pip install -e .`
5. Systemd service file written to `~/.config/systemd/user/spaid.service`
6. Autostart `.desktop` file for spaiOS written to `~/.config/autostart/spaios.desktop`
7. Default config created at `~/.config/spaish/spaid.toml` if not present
8. Final message: `✓ spaiOS ready. Press Super+Space or say your wake word.`

## Source path config (top of script)

```bash
SPAISH_DIR="${SPAISH_DIR:-$HOME/Development/spaiSH}"
SPAIOS_DIR="${SPAIOS_DIR:-$HOME/Development/spaiOS}"
```

Overridable via environment variables for CI or non-standard layouts.

## Files Touched

- `scripts/spai-install.sh` — new, executable

## Done When

- [x] `./scripts/spai-install.sh install` completes cleanly on fresh state
- [x] `spaid` systemd service running after install: `systemctl --user status spaid`
- [x] spaiOS autostart entry present: `~/.config/autostart/spaios.desktop`
- [x] `./scripts/spai-install.sh uninstall` removes all installed files, leaves config
- [x] `./scripts/spai-install.sh reinstall` = clean uninstall + fresh install
- [x] Missing dep prints helpful error (not a cryptic Go build failure)
- [x] Full cycle completes in under 2 minutes on dev machine (4s actual)
