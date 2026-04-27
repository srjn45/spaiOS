# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 1, Session 17

**Goal:** Begin Phase 2 — Voice Activation. Get `faster-whisper` transcription working
end-to-end: record audio on push-to-talk (`Super+Shift+Space`), transcribe, and send the
transcript to the existing Orchestrator as if the user had typed it.

**Steps (in order):**
1. Read `docs/phases/2026-04-26-phase-2-the-reach.md` — understand Phase 2 scope
2. Create task doc: `docs/tasks/YYYY-MM-DD-p2-voice-ptt.md`
3. Add `faster-whisper` and `sounddevice` to `pyproject.toml` dependencies
4. Implement `src/spaiOS/core/voice.py` — push-to-talk recording + transcription
5. Wire `Super+Shift+Space` hotkey in `hotkey.py` → start/stop recording
6. Overlay shows "Listening…" sphere state during recording
7. Transcript feeds into `Orchestrator.ask()` on key-release
8. Manual test: press hotkey, speak, verify transcription appears in overlay
9. Sync docs to Notion, commit

**Notion task:** phase2_m1_voice_ptt
**Task doc:** `docs/tasks/YYYY-MM-DD-p2-voice-ptt.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
