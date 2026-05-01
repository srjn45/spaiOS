# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 4 (Persistent Memory)

**Goal:** Build ChromaDB-backed memory that survives across overlay sessions. AI can answer
"what have I been working on?" and carry context forward automatically.

**Notion task:** phase2_m4_persistent_memory

**Done (M2 — Chrome App Control):**
- ChromeAgent: open_url, search_web, fill_form, click_link_by_text (partial match + buttons), get_tabs, clear_history
- fill_form E2E verified working. click_link_by_text fixed (partial match, includes buttons). get_tabs fixed (direct /json)
- Skipped M3 (system-wide input/AT-SPI) — deferred, will revisit after all other milestones
- 69/69 tests pass

**Plan:** `docs/superpowers/plans/2026-05-01-m4-persistent-memory.md`

**Steps (in order — follow the plan doc):**
1. Task 1: `uv add chromadb` + `ollama pull nomic-embed-text`
2. Task 2: MemoryStore — session_log (TDD)
3. Task 3: MemoryStore — user_profile (TDD)
4. Task 4: MemoryStore — context_snippets (TDD)
5. Task 5: summarize_session() using llama3.2:3b (TDD)
6. Task 6: Wire MemoryStore into Orchestrator (memory context in system prompt)
7. Task 7: Wire end_session() into Overlay hide paths (background thread)
8. Task 8: /remember slash command for manual snippets

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
