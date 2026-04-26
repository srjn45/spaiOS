# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 1 — Milestone 5, Session 13

**Goal:** Wire File Agent into the Orchestrator — "Organize my sandbox" → AI calls tools → proposes categories → user confirms → files moved.

**Steps (in order):**
1. Define Ollama function-calling schemas for all 6 File Agent tools in `src/core/orchestrator.py`
2. Orchestrator detects tool calls in Ollama response and dispatches to `FileAgent`
3. Tool result fed back to Ollama for final natural-language response
4. `delete_file` confirmation flow: when `DeleteConfirmationRequired` is raised, overlay displays a confirmation prompt; user response re-calls `delete_file(confirmed=True)`
5. Test end-to-end: "list my sandbox files" → AI sees directory listing
6. Test end-to-end: "organize my sandbox" → AI proposes folders → user confirms → files moved

**Notion task:** phase1_m5_file_agent (same task, continuing)
**Task doc:** `docs/tasks/2026-04-27-m5-orchestrator-routing.md` (create at session start)

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
