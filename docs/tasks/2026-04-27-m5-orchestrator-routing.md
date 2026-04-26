# Task: Wire File Agent into Orchestrator

**Date:** 2026-04-27
**Phase:** Phase 1 — Milestone 5, Session 13
**Session goal:** Orchestrator dispatches Ollama tool calls to FileAgent; delete requires user confirmation via the existing clarifying-question flow.
**Notion task:** phase1_m5_file_agent

## What We're Building

Teach the Orchestrator to use Ollama's function-calling API so the AI can directly operate on the sandbox filesystem. When the model emits a tool call, the Orchestrator dispatches it to FileAgent, feeds the result back to Ollama, and returns the final natural-language reply. Deletions require an explicit "yes" from the user before the file is touched.

## Approach

1. Define Ollama tool schemas for all 6 FileAgent methods in `orchestrator.py`
2. Add `FileAgent` instance to `Orchestrator.__init__`
3. Add `_pending_delete: str | None` state for the confirmation flow
4. Replace direct `ollama.chat()` call in `ask()` with `_run_with_tools()` that loops over tool calls
5. `_dispatch_tool()` routes each tool call to FileAgent; catches `DeleteConfirmationRequired` and sets `_pending_delete`
6. `ask()` short-circuits to `_handle_delete_response()` when `_pending_delete` is set
7. The confirmation reply ends with "?" → existing `is_clarifying_question` path turns sphere amber — no overlay changes needed
8. Clear `_pending_delete` in `clear_history()`

## Files Touched

- `src/spaiOS/core/orchestrator.py` — add tool schemas, tool-dispatch loop, delete confirmation state

## Done When

- `ask("list my sandbox files")` → AI calls `list_directory`, overlay shows file listing
- `ask("organize my sandbox")` → AI creates folders and moves files; sphere animates as it works
- AI attempting to delete a file → overlay goes amber with "Are you sure? (yes/no)"
- User types "yes" → file deleted; user types "no" → deletion cancelled
- `clear_history()` resets `_pending_delete` so state does not leak across sessions
