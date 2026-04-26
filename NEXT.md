# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 1, Session 1

**Goal:** GPU inference working via Ollama.

**Steps (in order):**
1. Fix NVIDIA driver: `sudo ubuntu-drivers autoinstall && sudo reboot`
2. Verify GPU post-reboot: `nvidia-smi` — driver version, 4GB VRAM shown
3. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
4. Pull models: `ollama pull llama3.2:3b && ollama pull moondream`
5. Verify GPU during inference: run `nvidia-smi` in a second terminal while `ollama run llama3.2:3b "hello"` is running — GPU memory should increase
6. Test moondream: take a screenshot with `scrot /tmp/test.png`, pass it to moondream via Ollama CLI, verify it describes the screen

**Session 2 continues with:** Python project skeleton (`uv init`, `pyproject.toml`, `src/` layout, Ollama SDK smoke test)

**Notion task:** [Milestone 1: Environment Setup](https://notion.so/34e7600e54c78140bdd8f41e364d4d1a)
**Task doc:** `docs/tasks/2026-04-26-m1-environment-setup.md`

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
