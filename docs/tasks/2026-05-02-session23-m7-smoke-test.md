# Task: M7 Live Smoke-Test (Session 23)

**Date:** 2026-05-02
**Phase:** Phase 2 — Milestone 7 (Custom Wake Word Setup)
**Session goal:** Manually verify AC9, AC10, AC11 against the running overlay. Document pass/fail.
**Notion task ID:** phase2_m7_wake_word_setup

## What We're Building
No new code — this is a live acceptance test session. We run the overlay, exercise the /wake-setup dialog and wake detection, and record results against three acceptance criteria.

## Approach
1. Start the overlay: `uv run spaiOS`
2. AC9: Type `/wake-setup` → wizard opens → record phrase 5× + 3 negatives → confirm `wake_profile.json` written
3. AC10: Say "Hi Spai" → overlay activates (OWW phonetic path)
4. AC11: Use custom phrase set in AC9 (e.g. "Cutto") → say it → overlay activates within ~4s
5. Document pass/fail for each AC
6. If any AC fails: note the failure mode, decide fix-or-defer
7. Commit task doc + smoke-test results

## Files Touched
- `docs/tasks/2026-05-02-session23-m7-smoke-test.md` — this file
- `docs/tasks/2026-05-02-session23-results.md` — pass/fail results (written after test)

## Results

**AC9: PASS** — `/wake-setup` wizard completed; `wake_profile.json` written correctly.

**AC10: DEFERRED** — "Hi Spai" did not trigger via OWW. Root cause: `hey_jarvis_v0.1` model is
phonetically trained for "hey jarvis" only; "hi spai" was silently ignored (mode was `oww_whisper`
but WhisperPollThread only watched `whisper_poll` phrases).
Fix applied this session:
- Removed "hi spai"/"hey spai" from `_OWW_COMPATIBLE` → new setups assign `whisper_poll` mode
- `WakeWordListener` now includes `oww_whisper` phrases in poll thread (existing profile works)
Re-test with: restart app, say "Hi Spai", watch `[WhisperPoll] heard:` terminal output.

**AC11: DEFERRED** — "Cutto" did not trigger. Root cause: calibration stored `whisper_target = "q2"`
(Whisper mishears made-up words); poll thread only matched against `whisper_target`, not the
original phrase.
Fix applied this session:
- `WhisperPollThread` now matches against both `whisper_target` AND original `phrase`
- Added `[WhisperPoll] heard:` debug print to terminal every 3s
Re-test with: restart app, say "Cutto", verify match in terminal output.
