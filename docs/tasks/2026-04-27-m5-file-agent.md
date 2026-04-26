# Task: File Agent Tools

**Date:** 2026-04-27
**Phase:** Phase 1 — The Spark
**Session goal:** Build standalone file management tools with sandbox isolation, tested via Python REPL.
**Notion task ID:** phase1_m5_file_agent

## What We're Building

A `FileAgent` class in `src/spaiOS/agents/file_agent.py` with six file management tools. All operations are confined to a configurable sandbox path (`~/spaiOS-sandbox/`). System paths are hard-blocked. Delete requires explicit confirmation before acting.

## Approach

1. Populate `sandbox/` with 20+ messy test files (mixed types, random names)
2. Implement `FileAgent` with `list_directory`, `create_folder`, `move_file`, `rename_file`, `delete_file`, `read_file_summary`
3. Path validation resolves symlinks and checks prefix against sandbox root
4. `delete_file` raises `DeleteConfirmationRequired` exception — caller must re-call with `confirmed=True`
5. System paths hard-blocked via a constant blocklist
6. Manual test via `python -c "..."` or short test script

## Files Touched

- `src/spaiOS/agents/file_agent.py` — new file, FileAgent class
- `sandbox/` — 20+ test files created
- `tests/test_file_agent.py` — unit tests

## Done When

- All 6 tools implemented and manually tested
- Path traversal outside sandbox returns a clear error
- System path blocked with clear error
- Delete without `confirmed=True` raises `DeleteConfirmationRequired`
- Delete with `confirmed=True` actually deletes
- `list_directory` returns structured list of entries
