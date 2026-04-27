# Task: Noise Cancellation + Silero VAD for Voice Pipeline

**Date:** 2026-04-27
**Phase:** Phase 2 — Milestone 1 (Voice Pipeline fix)
**Session goal:** Replace the fixed 6-second recording timeout with proper noise
cancellation (noisereduce) and neural end-of-speech detection (Silero VAD), so the
voice flow reliably terminates when the user stops speaking regardless of fan/ambient noise.
**Notion task:** phase2_m1_voice_pipeline

---

## Why This Exists

During Session 19 testing we discovered that energy-based silence detection is
unreliable on the HP Omen laptop. The fan noise RMS (0.09–0.15) and speech RMS
(0.14–0.24) overlap, so no fixed threshold cleanly separates them. A 6-second
fixed recording window was shipped as a temporary workaround.

The proper fix has two parts:

1. **noisereduce** — spectral subtraction to strip the stationary fan noise from
   the captured audio before sending to Whisper. Fan noise is ideal for this because
   it is constant-frequency (stationary), so a one-time noise profile measured at
   startup can be subtracted from all subsequent audio.

2. **Silero VAD** — a tiny (~2 MB) ONNX neural network trained to recognise human
   speech phoneme patterns. Unlike RMS thresholding, it is robust to fan/HVAC noise
   because it looks at spectral shape and temporal patterns, not amplitude alone.

---

## Approach

### Step 1 — Install dependencies
```bash
uv add noisereduce silero-vad
# silero-vad pulls in torch; verify it fits within available RAM (~7-8GB free)
# If torch is too heavy, use the ONNX-only silero VAD:
#   uv add onnxruntime  # already installed via openwakeword
#   download silero_vad.onnx manually
```

### Step 2 — Noise profile calibration at startup
In `WakeWordListener.run()`, before entering the main loop, record ~1.5s of audio
while the user is silent (or use the first few OWW chunks before any speech is
detected). Store the numpy float32 array as `_noise_profile`.

```python
# Capture ~1.5s of ambient noise at startup for profiling
noise_frames = []
for _ in range(int(1.5 * _SAMPLE_RATE / _OWW_CHUNK)):
    data, _ = stream.read(_OWW_CHUNK)
    noise_frames.append(np.frombuffer(bytes(data), dtype="int16").astype(np.float32) / 32768.0)
noise_profile = np.concatenate(noise_frames)
```

### Step 3 — Apply noisereduce before Whisper transcription
In `AudioTranscribeThread.run()` (or before emitting `audio_ready`), apply:

```python
import noisereduce as nr
cleaned = nr.reduce_noise(y=audio, sr=_SAMPLE_RATE, y_noise=noise_profile)
```

`audio_ready` should emit the cleaned array, or `AudioTranscribeThread` should
receive both the raw audio and the noise profile.

### Step 4 — Silero VAD for end-of-speech detection
Replace the fixed `_UTTERANCE_MAX = 6s` with Silero VAD:

```python
from silero_vad import load_silero_vad, get_speech_timestamps

vad_model = load_silero_vad()

# After accumulating utterance, run VAD to detect end-of-speech
# Feed 512-sample chunks (32ms at 16kHz) to the VAD model
# When VAD returns no speech for >1s, emit audio_ready
```

Silero VAD's `get_speech_timestamps` can also be used post-hoc on the full utterance
to trim leading/trailing silence before Whisper, improving transcription accuracy.

### Step 5 — Wire together
The full updated pipeline in `WakeWordListener.run()`:

```
1. Startup: record noise_profile (1.5s)
2. Wake detection loop (OWW, 1280-sample chunks):
   - Feed chunk to OWW → if score ≥ 0.5, switch to utterance mode
3. Utterance mode:
   - Accumulate audio chunks
   - Feed to Silero VAD in 512-sample windows
   - When VAD detects ≥1s of silence: stop, emit audio_ready(cleaned_audio)
   - Hard timeout: 12s max (safety net, not primary mechanism)
4. AudioTranscribeThread:
   - Apply noisereduce with stored noise_profile
   - Run Whisper on cleaned audio
```

### Step 6 — Pass noise profile to AudioTranscribeThread
`AudioTranscribeThread` needs the noise profile to clean audio. Options:
- Module-level `_noise_profile: np.ndarray | None = None` set at startup
- Or pass as constructor arg: `AudioTranscribeThread(audio, noise_profile)`

Prefer the constructor arg to avoid global mutable state.

### Step 7 — Tests
- Unit test: `noisereduce` reduces RMS of a sine-wave + white-noise mix
- Unit test: Silero VAD returns True for a speech-like signal, False for silence
- Integration: full pipeline with mock audio doesn't regress existing tests

---

## Files Touched
- `src/spaiOS/core/voice.py` — main changes (WakeWordListener, AudioTranscribeThread)
- `tests/test_voice.py` — new VAD and noise reduction tests
- `pyproject.toml` — new deps (noisereduce, silero-vad or onnxruntime path)

## Done When
- [ ] Say "hey Jarvis" → ask a question → overlay responds within ~2s of the user
  stopping speech (not a fixed 6s wait)
- [ ] Whisper transcription is accurate (fan noise not garbling output)
- [ ] After overlay closes, wake word detection resumes immediately
- [ ] All existing tests pass
- [ ] No fixed timeout required (12s hard-cap only as safety net)
