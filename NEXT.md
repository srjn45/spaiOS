# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 5, Session 12

**Goal:** Build File Agent tools standalone — all file management functions implemented and tested directly in Python, sandbox folder populated with 20+ messy test files.

**Steps (in order):**
1. Populate `sandbox/` with 20+ messy test files (mixed types, random names, no organization)
2. `src/spaiOS/agents/file_agent.py` — implement `list_directory`, `create_folder`, `move_file`, `rename_file`, `delete_file`, `read_file_summary`
3. All paths validated to resolve under `~/spaiOS-sandbox/` (or configured base path)
4. `delete_file` must always prompt for confirmation before acting — emit a signal or raise an exception that the caller handles; no silent deletes
5. System paths (`/etc`, `/usr`, `/bin`, `/boot`) hard-blocked regardless of input
6. Manually test each tool from a Python REPL or short test script

**Notion task:** (create in Notion at session start)
**Task doc:** `docs/tasks/2026-04-27-m5-file-agent.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
