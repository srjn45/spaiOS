# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 5 (Remaining Agents + Config)

**Goal:** Build Code Agent, Media Agent, and MCP config system so the "First Five" PRD scenarios can all run end-to-end.

**Notion task:** phase2_m5_agents_config

**Done (M4 — Persistent Memory):**
- MemoryStore: session_log, user_profile, context_snippets (ChromaDB-backed, TDD)
- summarize_session() using llama3.2:3b
- Orchestrator: accepts memory, injects last 5 sessions into system prompt, end_session() on hide
- Overlay: MemoryStore created on init, end_session() in background thread on toggle/idle/Escape
- /remember slash command for manual snippets
- 89/89 tests pass

**Plan:** Write plan doc before starting: `docs/superpowers/plans/YYYY-MM-DD-m5-agents-config.md`

**Steps (in order — write plan first):**
1. Task 1: Code Agent — read_file, write_file (diff + confirm), run_terminal_command, open_in_editor
2. Task 2: Media Agent — apply_filter ("90s_film", "vintage", "high_contrast", "black_white")
3. Task 3: MCP config — config.toml provider switching (ollama / anthropic / openai)
4. Task 4: "First Five" PRD scenarios E2E acceptance test

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
