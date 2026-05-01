# Task: Code Agent

**Date:** 2026-05-01
**Phase:** Phase 2 — Milestone 5 (Remaining Agents + Config)
**Session goal:** Build CodeAgent with read_file, write_file (diff + confirm), run_terminal_command, and open_in_editor; wire into Orchestrator.
**Notion task:** phase2_m5_agents_config

## What We're Building

`src/spaiOS/agents/code_agent.py` — a code-focused agent that can read any file, write files with a diff-preview + confirmation gate (same pattern as delete), run shell commands in a subprocess with a dangerous-command blocklist, and open a file in the user's $EDITOR.

## Approach

1. Write failing tests in `tests/test_code_agent.py` (TDD — RED first)
2. Implement `CodeAgent` with `WriteConfirmationRequired` and `CommandBlocked` exceptions
3. Watch all tests go GREEN
4. Add `_CODE_TOOLS` spec + dispatch to `src/spaiOS/core/orchestrator.py`
5. Add write-confirmation flow to Orchestrator (mirrors delete-confirmation)
6. Update `_BASE_SYSTEM_PROMPT` to mention code tools
7. Run full suite — confirm 89 existing + new tests pass

## Files Touched

- `tests/test_code_agent.py` — new test file (~12 tests)
- `src/spaiOS/agents/code_agent.py` — new agent
- `src/spaiOS/core/orchestrator.py` — wire CodeAgent, add write-confirm flow

## Done When

- `read_file(path)` returns file content; raises `FileNotFoundError` for missing paths
- `write_file(path, content)` raises `WriteConfirmationRequired` with a unified diff
- `confirm_write(path, content)` actually writes the file
- `run_terminal_command(cmd)` runs cmd in subprocess; blocks `rm -rf /`, `mkfs.*`, etc.; returns stdout+stderr; times out gracefully
- `open_in_editor(path)` launches `$EDITOR path` via Popen
- Orchestrator routes the four tools; write confirmation ("yes"/"no") flow works like delete confirmation
- All tests pass: `uv run pytest tests/ -q`
