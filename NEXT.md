# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 1 Fix (noise cancellation + VAD)

**Goal:** Replace the fixed 6-second recording timeout with proper noise cancellation
(noisereduce) and Silero VAD end-of-speech detection, so the voice pipeline
terminates reliably when the user stops speaking regardless of laptop fan noise.

**Task doc:** `docs/tasks/2026-04-27-p2-noise-cancellation-vad.md`
**Notion task:** phase2_m1_voice_pipeline

**Steps (in order):**
1. Install deps: `uv add noisereduce silero-vad` — verify RAM fits (~7-8GB free)
   - If torch too heavy, use ONNX path for Silero VAD (onnxruntime already present)
2. Add startup noise profile calibration (record 1.5s ambient before main loop)
3. Wire Silero VAD into utterance mode — replace fixed 6s timeout with VAD silence detection
4. Apply noisereduce in `AudioTranscribeThread` before Whisper (pass noise profile as arg)
5. Add 12s hard-cap as safety net (not primary mechanism)
6. Write tests: VAD smoke test, noisereduce reduces RMS on synthetic data
7. Run `uv run pytest` — all pass
8. Manual test: say "hey Jarvis", ask question, confirm response arrives within ~2s of stopping speech
9. If all criteria met: update Notion task Status → Done, move NEXT.md to Phase 2 Milestone 2

**Known risks:**
- silero-vad pulls in PyTorch — verify it doesn't OOM on 7-8GB available RAM
- If torch is too large, use the ONNX-only Silero VAD path (download silero_vad.onnx directly)

---

## After this fix: Phase 2 — Milestone 2 (Chrome App Control)

Once the voice pipeline is solid, continue with the original Phase 2 queue:
- Milestone 2: Chrome/browser app control
- Milestone 3: System input
- (see `docs/phases/2026-04-26-phase-2-the-reach.md` for full breakdown)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
