# Task: Milestone 1 — Environment Setup

**Date:** 2026-04-26
**Phase:** Phase 1 — The Spark
**Sessions:** 1–2 (~4hrs)
**Notion task ID:** 34e7600e54c78140bdd8f41e364d4d1a

## What We're Building

GPU inference via Ollama on the HP Omen's GTX 1050 Ti, confirming llama3.2:3b and moondream are accessible via Python SDK. Then the Python project skeleton: pyproject.toml managed by uv, the src/ directory layout, and a passing smoke test that confirms end-to-end Ollama connectivity and vision description from a screenshot.

## Approach

1. Fix NVIDIA driver: `sudo ubuntu-drivers autoinstall && sudo reboot`
2. Verify GPU: `nvidia-smi` — confirm driver version, 4GB VRAM visible
3. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
4. Pull models: `ollama pull llama3.2:3b && ollama pull moondream`
5. Verify GPU during inference: `nvidia-smi` in another terminal while `ollama run llama3.2:3b "hello"` runs — GPU memory should rise
6. Init project: `uv init spaiOS` → set Python 3.12, configure pyproject.toml
7. Add dependencies: `uv add ollama pillow pyqt6 pyatspi pynput python-xlib`
8. Create src/ layout: `ui/`, `core/`, `agents/`, `main.py`
9. Write smoke test: one-shot `ollama.chat('llama3.2:3b', ...)` call, print response
10. Write vision test: `scrot` screenshot → `PIL.Image.open()` → base64 → moondream → print description
11. Create `sandbox/` with 20+ messy test files for File Agent later

## Files Touched

- `pyproject.toml` — project metadata, dependencies, entry point
- `src/main.py` — entry point (skeleton)
- `src/ui/` — directory created (empty)
- `src/core/` — directory created (empty)
- `src/agents/` — directory created (empty)
- `sandbox/` — populated with test files

## Done When

1. `nvidia-smi` shows GPU memory usage while `ollama run llama3.2:3b "hello"` is running
2. `ollama pull llama3.2:3b` and `ollama pull moondream` complete without error
3. Python: `ollama.chat('llama3.2:3b', messages=[{'role':'user','content':'say hi'}])` returns a response
4. moondream receives a `scrot` screenshot as base64 and returns a text description of the screen
5. `uv run python src/main.py` exits cleanly (skeleton entry point)
