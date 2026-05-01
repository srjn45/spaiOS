# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 2 — Milestone 5 (Remaining Agents + Config)

**Goal:** Build Media Agent and MCP config system so the "First Five" PRD scenarios can all run end-to-end.

**Notion task:** phase2_m5_agents_config

**Done (M5 Session 14 — Code Agent):**
- CodeAgent: read_file, write_file (diff + confirm via WriteConfirmationRequired), run_terminal_command (blocklist + timeout), open_in_editor
- Orchestrator: _CODE_TOOLS registered, write-confirmation flow wired (mirrors delete-confirm), _pending_write state
- 105/105 tests pass

**Done (M5 Session 15 — Media Agent):**
- MediaAgent: apply_filter (90s_film, vintage, high_contrast, black_white), get_image_info, resize_image
- 90s_film = 20% desaturation + grain (numpy) + vignette + warm shift
- Orchestrator: _MEDIA_TOOLS registered, dispatch wired for all three tools
- 129/129 tests pass

**Steps (remaining):**
1. Task 3: MCP config — config.toml provider switching (ollama / anthropic / openai)
2. Task 4: "First Five" PRD scenarios E2E acceptance test

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
