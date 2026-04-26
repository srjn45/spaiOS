# Task: Milestone 5 — File Agent

**Date:** 2026-04-26
**Phase:** Phase 1 — The Spark
**Sessions:** 12–15 (~8hrs)
**Notion task ID:** 34e7600e54c781c3a8ddd0cf79bc8cc8

## What We're Building

`src/agents/file_agent.py`: all six file management tools operating exclusively within `~/spaiOS-sandbox/`. The Orchestrator routes Ollama tool calls to File Agent functions. A confirmation flow renders destructive-op prompts in the overlay. Path validation blocks escapes from the sandbox and hard-blocks system paths regardless of user input.

## Approach

**Session 12 — Tool functions standalone:**
1. `SANDBOX_ROOT = Path.home() / "spaiOS-sandbox"` constant
2. `validate_path(path: str) -> Path`: resolve, check `.is_relative_to(SANDBOX_ROOT)`, raise `SandboxViolationError` if not
3. `list_directory(path: str) -> dict` — `os.scandir`, return `{name, size, type, modified}` per entry
4. `create_folder(path: str, name: str) -> str` — `mkdir(exist_ok=True)`
5. `move_file(src: str, dst: str) -> bool` — `shutil.move`, validate both paths
6. `rename_file(path: str, new_name: str) -> bool`
7. `delete_file(path: str) -> bool` — does NOT delete; raises `ConfirmationRequired` exception
8. `read_file_summary(path: str) -> str` — read first 500 chars
9. Populate `sandbox/` with 20+ messy files (mixed extensions, no structure)
10. Test each function directly in a REPL

**Session 13 — Orchestrator routing:**
11. Register all tool functions in Orchestrator's `TOOL_DEFS` and dispatch table
12. "Organize my sandbox" → AI calls `list_directory` → proposes categories → ask_clarification "Shall I create these folders and move the files?" → on yes → calls `create_folder` × N → `move_file` × M
13. Test full organize flow end-to-end in overlay

**Session 14 — Safety mechanisms:**
14. `delete_file` raises `ConfirmationRequired(path, "This cannot be undone.")`; Orchestrator catches → emits `confirmation_requested` signal → overlay shows dialog
15. User clicks Yes/No in overlay → signal returned to Orchestrator → proceed or abort
16. Last-action undo: `_last_moves: list[tuple[src, dst]]` stored per session; `undo_last()` reverses them
17. Test: `../../etc/passwd` attempt → `SandboxViolationError` displayed in overlay

**Session 15 — Error handling:**
18. `FileNotFoundError`, `PermissionError` → `FileAgentError(friendly_message)` surfaced to overlay
19. Partial failure during bulk move: log which files succeeded, report failures without crashing
20. Test: remove a file mid-organize, verify error message appears and remaining ops continue

## Files Touched

- `src/agents/file_agent.py` — all tool functions + safety
- `src/core/orchestrator.py` — route tool calls, confirmation signal
- `src/ui/overlay.py` — confirmation dialog, undo button
- `sandbox/` — 20+ messy test files

## Done When

1. "organize my sandbox" → AI proposes categories → user confirms → files correctly moved into subfolders
2. `delete_file` always emits confirmation dialog before any deletion
3. Path outside sandbox (`/etc`, `~/Documents`) → friendly "Operation not permitted outside sandbox" message
4. `../../etc/passwd` path traversal → blocked at `validate_path()`
5. "undo last action" → moved files returned to original locations
