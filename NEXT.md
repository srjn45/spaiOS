# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 7 (Session 23: Live Smoke-Test)

**Goal:** Live smoke-test of M7 acceptance criteria AC9, AC10, AC11. Document results.

**Notion task:** phase2_m7_wake_word_setup

**Done (M7 Sessions 21–22 — complete):**
- Session 21+22 (combined): Full TDD implementation — WakeProfileStore, save_wav, WakeSampleThread,
  wake_trainer (Whisper calibration), WakeSetupDialog (5-sample wizard), WhisperPollThread,
  multi-phrase WakeWordListener, /wake-setup overlay command, poll_wake signal wiring in main.py.
  194 tests, all green.

**Steps (remaining):**
1. Session 23: Live smoke-test:
   - AC9: type `/wake-setup` → dialog opens → record phrase 5× + 3 negatives → check `wake_profile.json` written
   - AC10: say "Hi Spai" → overlay activates (OWW phonetic detection)
   - AC11: set up custom phrase (e.g. "Cutto") → say it → overlay activates within ~4 seconds
   Document pass/fail for each.
2. Session 24: Phase 2 retrospective doc, update Notion, write Phase 3 session breakdown.

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
