# Task: P3-M5 — Full Loop Polish

**Date:** 2026-05-03
**Phase:** Phase 3 — The Assistant Layer
**Session goal:** End-to-end demo hardening. Fix rough edges, run all Phase 3 acceptance criteria.
**Notion task ID:** phase3_m5_full_loop_polish

## What We're Building

No new features. Fix integration rough edges found during M1–M4 testing, update docs, and verify all Phase 3 acceptance criteria pass cleanly on a fresh install.

## Expected Polish Items (discovered during M1–M4)

- Error handling: overlay shows friendly message when spaid unreachable
- Error handling: graceful failure when xdotool/wmctrl target window disappears mid-action
- Session continuity: overlay queries share session context across invocations
- Timing: sphere animation syncs with spaid response stream start/end
- Edge case: "close this window" when no window is focused
- Edge case: wake word triggers while spaid is processing a previous request
- Config: first-run experience if neither API key nor Ollama is configured
- Docs: update CLAUDE.md session start ritual to reflect new architecture
- Docs: update README with new install instructions

## Acceptance Criteria (Phase 3 complete when all pass)

- [ ] AC1: `Super+Space` → "snap Firefox to the left" → Firefox snaps to left half
- [ ] AC2: Wake word → overlay activates → "open terminal" → terminal launches
- [ ] AC3: `spai explain why my build failed` in terminal still works (no spaiSH regression)
- [ ] AC4: Disconnect internet mid-session → next query falls back to local Ollama, no crash
- [ ] AC5: `./scripts/spai-install.sh reinstall` completes cleanly in < 2 minutes
- [ ] AC6: Fresh install on Ubuntu 24.04 GNOME → all of the above work

## Files Touched

- Various bug fixes across `spaid_client.py`, `orchestrator.py`, spaiSH tools
- `CLAUDE.md` — update session start ritual
- `README.md` — new install instructions
- `NEXT.md` — point to Phase 4 planning
