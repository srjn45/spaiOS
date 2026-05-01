# Task: Media Agent

**Date:** 2026-05-01
**Phase:** Phase 2 — The Reach
**Session goal:** Build MediaAgent with four image filters so the "make this look like a 90s film" scenario works end-to-end.
**Notion task ID:** phase2_m5_agents_config

## What We're Building

PIL/numpy-based image processing agent. Supports four filter styles:
`90s_film`, `vintage`, `high_contrast`, `black_white`. Also exposes `get_image_info` and `resize_image`.
Wired into the Orchestrator so the LLM can invoke `apply_filter` via tool call.

## Approach

1. Create `src/spaiOS/agents/media_agent.py` with `MediaAgent` class
2. Implement `black_white` (grayscale) and `high_contrast` (contrast enhance)
3. Implement `vintage` (partial desaturate + warm tint)
4. Implement `90s_film` (desaturate 20% + grain + vignette + warm shift)
5. Implement `get_image_info` and `resize_image`
6. Add `_MEDIA_TOOLS` to orchestrator and dispatch
7. Update system prompt to mention `apply_filter`, `get_image_info`, `resize_image`
8. Write `tests/test_media_agent.py` covering all filters and edge cases
9. Run lint + tests
10. Update NEXT.md and commit

## Files Touched

- `src/spaiOS/agents/media_agent.py` — new file
- `src/spaiOS/core/orchestrator.py` — add tools + dispatch
- `tests/test_media_agent.py` — new test file
- `NEXT.md` — update after task completes

## Done When

- All four filters produce a valid output image file (JPEG)
- Output saved alongside input with `_<style>` suffix
- Unknown style raises `ValueError`
- Missing input file raises `FileNotFoundError`
- Tests pass: `uv run pytest tests/test_media_agent.py -v`
- Orchestrator dispatches `apply_filter` calls correctly
