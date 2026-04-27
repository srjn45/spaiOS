# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 1, Session 18

**Goal:** Add always-on wake word detection. Background thread listens continuously for
"hey spaiOS" using vosk (offline), then activates the overlay and starts recording without
requiring a keyboard hotkey.

**Steps (in order):**
1. Create task doc: `docs/tasks/YYYY-MM-DD-p2-wake-word.md`
2. Add `vosk` to `pyproject.toml`; download vosk small model (~50MB)
3. Implement wake word listener in `src/spaiOS/core/voice.py` — background thread,
   uses vosk to detect "hey spaiOS", fires callback on match
4. Add microphone privacy indicator to overlay (small dot in corner when mic active)
5. Wire wake word callback in `main.py` → show overlay + start recording
6. End-of-utterance detection: 1.5s silence → stop recording + transcribe
7. Manual test: say "hey spaiOS, what time is it?" without touching keyboard
8. Sync docs to Notion, commit

**Notion task:** phase2_m1_voice_pipeline
**Task doc:** `docs/tasks/YYYY-MM-DD-p2-wake-word.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
