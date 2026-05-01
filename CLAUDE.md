# spaiOS — Claude Development Guide

This file is read at the start of every Claude session. It defines how we work, what patterns to follow, and what to avoid.

---

## Session Start Ritual (Do This First)

1. Read `docs/superpowers/specs/2026-04-26-spaiOS-design.md` — project overview and quick context
2. Read the current phase doc in `docs/phases/` (highest phase number that is not complete)
3. Check git log: `git log --oneline -10` — understand what was done last session
4. Ask the user which Notion task we're picking up, or check the task board
5. Create a task doc: `docs/tasks/YYYY-MM-DD-<task-name>.md` before writing any code

---

## Development Lifecycle

Each 2-hour session follows this structure:

```
[0:00–0:10]  Orient: read phase doc + git log + task from Notion
[0:10–0:15]  Write task doc (docs/tasks/YYYY-MM-DD-<task>.md)
[0:15–1:45]  Implement the focused component
[1:45–1:55]  Run lint + test acceptance criteria for the component
[1:55–2:00]  Commit all changes, sync Notion docs if any docs/ changed
```

**One component per session.** Do not try to build multiple things in one session. Focused, testable increments.

---

## Doc Sync Workflow

**Repo markdown = source of truth for AI context**
**Notion = human-readable mirror**

Rules:
- Every decision, RFC, spec, and task plan lives in the repo as markdown AND in Notion as a page
- They must stay in sync — any change to `docs/` must be reflected in Notion before the session ends
- Use Notion MCP tools (once configured) to push changes at end of session
- `docs/notion-map.json` maps local doc paths to Notion page IDs (created during Notion setup)

**Sync trigger:** Any `git commit` that touches `docs/` should be followed by a Notion sync.

**How to sync:** Read changed markdown files → use Notion MCP `update_block` or `create_page` to mirror content. See `scripts/sync-notion.py` once written.

---

## Writing Task Docs

Before writing any code, create `docs/tasks/YYYY-MM-DD-<task-name>.md`:

```markdown
# Task: <Component Name>

**Date:** YYYY-MM-DD
**Phase:** Phase N — <Phase Name>
**Session goal:** One sentence describing the outcome of this session.
**Notion task ID:** <ID from task board>

## What We're Building
[2–4 sentences on the specific component]

## Approach
[Step-by-step implementation plan, 5–10 steps]

## Files Touched
- `src/path/to/file.py` — what changes

## Done When
[Specific, testable acceptance criteria for this session]
```

---

## Testing

**Phase 1–2 (Python):** No formal test framework. Test each component manually per its acceptance criteria.

Lint before every commit:
```bash
black src/ --check          # format check
flake8 src/ --max-line-length=100  # lint
```

Auto-format:
```bash
black src/
```

Run the overlay:
```bash
uv run spaiOS
# or: uv run python src/spaiOS/main.py
# NOTE: plain `python src/main.py` is wrong path; plain `spaiOS` requires activated venv
```

Test Ollama connection:
```bash
ollama run llama3.2:3b "hello"
nvidia-smi   # verify GPU is being used during inference
```

---

## Coding Standards

**Python:**
- Black formatting, 100-character line limit
- Type hints on all function signatures: `def capture() -> dict:`
- No docstrings for obvious functions. Docstring only if the WHY is non-obvious.
- No comments explaining WHAT code does — use clear names instead
- f-strings for string formatting

**Naming:**
- Files and modules: `snake_case.py`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

**Imports:** stdlib → third-party → local, separated by blank lines.

**Error handling:** Catch specific exceptions, not bare `except:`. Surface errors to overlay UI with a friendly message.

---

## Git Conventions

**Commit after every meaningful unit:** After a component works (not after every file save).

**Commit message format:** Imperative present tense, under 72 chars.
```
Add Neural Sphere idle pulse animation
Fix AT-SPI tree reader crashing on non-accessible apps
Update Phase 1 session breakdown with clearer milestones
```

**Never commit:**
- `config.toml` with real API keys (add to `.gitignore`)
- Model weight files (too large, add to `.gitignore`)
- `.env` files or any credentials

**All context committed:** Docs, decisions, task plans — nothing left uncommitted at session end. The repo is the full record of the project.

**Branch strategy:** `main` only for now. Feature branches when multiple people contribute (Phase 3+).

---

## Architecture Constraints

These are hard rules derived from `docs/rfcs/`. Do not violate them.

**Do not:**
- Pull `llama3.1:8b` or any model requiring more than 2.5GB VRAM (GTX 1050 Ti = 4GB, need headroom for vision model)
- Perform file operations outside `~/spaiOS-sandbox/` without explicit user approval in the conversation
- Modify Linux kernel source code (ever)
- Add cloud API calls without user setting `config.toml` and opting in
- Use `import *` or global mutable state
- Write synchronous Ollama calls on the Qt main thread (will freeze UI) — always use `QThread` or `asyncio`

**Always:**
- Ask one clarifying question before taking destructive actions (delete, overwrite)
- Show a diff before writing to any file the user didn't explicitly create this session
- Check that Ollama is running before any inference call, show friendly error if not
- Constrain file agent operations to the sandbox path

---

## File Naming

| Type | Convention | Example |
|------|-----------|---------|
| New doc (any) | `YYYY-MM-DD-<name>.md` | `2026-05-10-add-voice-wakeword.md` |
| Task doc | `docs/tasks/YYYY-MM-DD-<task>.md` | `docs/tasks/2026-05-01-neural-sphere-animation.md` |
| RFC | `docs/rfcs/YYYY-MM-DD-NNN-<topic>.md` | `docs/rfcs/2026-05-15-006-memory-schema.md` |
| Source file | `snake_case.py` | `file_agent.py` |

When creating a new RFC, increment the three-digit number from the last one in `docs/rfcs/`.

---

## Hardware Reference (HP Omen)

- CPU: i7-7700HQ, 4 cores / 8 threads, max 3.8GHz
- RAM: 16GB (typically 7–8GB available when OS + apps running)
- GPU: NVIDIA GTX 1050 Ti Mobile — **4GB VRAM**
- Disk: 102GB partition, ~17GB free (as of April 2026)
- OS: Ubuntu 24.04 LTS

**NVIDIA driver:** Version mismatch present. Fix before Session 1: `sudo ubuntu-drivers autoinstall && sudo reboot`

---

## Notion Setup

Notion MCP is required for doc sync. Once set up, Claude can create and update Notion pages automatically.

See `docs/notion-setup.md` for setup instructions.
Notion page IDs are stored in `docs/notion-map.json` (created during setup).
