# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 1, Session 19

**Goal:** Manual end-to-end test of wake word + transcription flow, then tune wake phrase
variants based on what vosk actually produces. If all criteria pass, close Milestone 1.

**Steps (in order):**
1. Run `spaiOS` — confirm "[spaiOS] Wake word listener active" prints and mic dot appears
2. Say "hey spaiOS" — confirm overlay shows and sphere enters listening state
3. Speak a sentence — confirm 1.5s silence triggers transcription and LLM responds
4. Note what vosk actually transcribes for "hey spaiOS" (may differ — add to `_WAKE_VARIANTS`)
5. If mis-transcription found: add variant to `_WAKE_VARIANTS` in voice.py + matching test
6. Run full test suite: `uv run pytest`
7. If all acceptance criteria met: update Notion task Status → Done, move NEXT.md to Milestone 2

**Notion task:** phase2_m1_voice_pipeline
**Known risk:** vosk may not reliably hear "spaiOS" — be ready to expand `_WAKE_VARIANTS`

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
