# Phase 2: The Reach

**Status:** Not started — begins after Phase 1 acceptance criteria pass
**Target:** Weeks 6–16 (~20–25 sessions × 2hrs = 40–50hrs)
**Output:** spaiOS Overlay with voice activation, Chrome app control, persistent memory, all core agents

---

## Goal

Transform the Phase 1 prototype into a genuinely useful daily tool. Add voice activation so the overlay requires no keyboard, the ability to control running applications (especially Chrome) on the user's behalf, persistent memory that survives across sessions, and the full set of specialized agents covering the PRD "First Five" scenarios.

**Showcase scenarios:**
- Voice: "hey spaiOS, open YouTube and search for lo-fi beats" → Chrome navigates without keyboard
- App control: "enter that I'm above 18" while an age-gate is on screen → AI clicks the correct button
- Memory: "what have I been working on this week?" → AI recalls from ChromaDB session log
- Workspace: "set me up for the Tokyo project" → creates folder structure, opens editor

---

## New Components (added to Phase 1 base)

### 1. Voice Activation (`src/core/voice.py`)

**Library:** `faster-whisper` for transcription, `pvporcupine` or `vosk` for always-on wake word detection.

**Flow:**
1. Background thread listens on default microphone continuously (low CPU wake word model only)
2. Wake phrase "hey spaiOS" detected → overlay activates, recording starts (indicator shown)
3. User speaks → silence for 1.5s signals end of utterance
4. faster-whisper transcribes audio clip → text sent to Orchestrator
5. Voice response: TTS via `pyttsx3` (optional — text in overlay is primary)

**Wake phrase config:** Set in `config.toml`. Default: "hey spaiOS". Can be changed by user.

**Push-to-talk fallback:** `Super+Shift+Space` for environments where always-on mic is unwanted (meetings, public spaces).

**Microphone privacy indicator:** Small LED-style dot shown in corner of screen when mic is active.

### 2. App Control Agent (`src/agents/app_control_agent.py`)

Two interaction paths combined into one agent:

**Path A — Chrome DevTools Protocol (CDP):**
Connect to Chrome's debug interface via WebSocket. Chrome must be launched with `--remote-debugging-port=9222`. Launch script provided in `scripts/launch-chrome.sh`.

Available actions via CDP:
```python
open_url(url: str)
navigate_back() / navigate_forward()
click_element(css_selector: str)
fill_input(css_selector: str, value: str)
get_page_content() -> str          # full page text
get_current_url() -> str
clear_history()
get_open_tabs() -> list[dict]
run_javascript(code: str) -> any   # for complex interactions
```

**Path B — System-wide Input (ydotool):**
ydotool daemon (`ydotoold`) runs as background service. Python calls via subprocess.

```python
click_at(x: int, y: int)
type_text(text: str)
key_combo(keys: str)              # e.g. "ctrl+c", "super+l"
move_mouse_to(x: int, y: int)
scroll(direction: str, amount: int)
```

**Routing logic:** Orchestrator identifies target app from context. If Chrome is focused → use CDP. Otherwise → use AT-SPI to identify clickable elements + ydotool to interact.

**The "I'm above 18" scenario:**
1. User on age-gated page → "hey spaiOS, confirm I'm above 18"
2. Orchestrator calls `get_page_content()` via CDP → finds confirm button selector
3. Calls `click_element("#age-confirm-btn")` → button clicked

### 3. Persistent Memory (`src/core/memory.py`)

**Library:** ChromaDB with `nomic-embed-text` embeddings via Ollama.

**Collections:**

`user_profile` — written once, updated rarely:
```python
{
  "name": "Srajan",
  "preferences": ["dark themes", "lo-fi music while coding"],
  "recurring_apps": ["code", "chrome", "terminal"],
  "timezone": "IST"
}
```

`session_log` — one entry per session:
```python
{
  "date": "2026-05-10",
  "duration_mins": 118,
  "summary": "Worked on Python file organizer script in VS Code. Researched FastAPI docs.",
  "apps_used": ["code", "chrome"],
  "tasks_completed": ["organized downloads folder", "read FastAPI tutorial"]
}
```

`context_snippets` — important things seen on screen:
```python
{
  "type": "error",
  "content": "ZeroDivisionError in src/utils.py line 42",
  "app": "code",
  "resolved": true,
  "date": "2026-05-08"
}
```

**On session start:** Load last 5 session summaries → inject into Orchestrator system prompt.

**On session end:** AI generates 2–3 sentence summary → stored in `session_log`. Triggered when user says "bye" or closes overlay.

### 4. Browser Agent (`src/agents/browser_agent.py`)

Wraps CDP tools in intent-oriented functions:
```python
search_web(query: str)                    # opens default search engine
open_url(url: str)
read_current_page() -> str                # get page text for summarization
fill_form(fields: dict[str, str])         # fill multiple form fields at once
click_link_by_text(link_text: str)        # semantic click by visible label
clear_history()
get_tabs() -> list
```

### 5. Code Agent (`src/agents/code_agent.py`)

```python
read_file(path: str) -> str
write_file(path: str, content: str)       # always shows diff before writing
run_terminal_command(cmd: str) -> str     # runs in sandboxed subprocess
open_in_editor(path: str)                 # opens in $EDITOR
explain_code(code: str, error: str) -> str
suggest_fix(code: str, error: str) -> str
```

**Safety:** `write_file` always renders a diff in the overlay and asks confirmation before saving.

### 6. Media Agent (`src/agents/media_agent.py`)

PIL-based image processing for the "First Five" photo filter scenario:
```python
apply_filter(image_path: str, style: str) -> str   # returns output path
# styles: "90s_film", "vintage", "high_contrast", "black_white"
get_image_info(path: str) -> dict
resize_image(path: str, width: int, height: int) -> str
```

"90s film" filter = desaturate 20% + add grain overlay + vignette + warm color shift.

### 7. MCP Integration (`src/core/mcp_client.py`)

Config-driven model switching. User can plug in API keys to use cloud models when local isn't sufficient.

`config.toml`:
```toml
[model]
provider = "ollama"                         # "ollama" | "anthropic" | "openai"
model = "llama3.2:3b"
fallback_provider = "anthropic"             # used if local model fails
fallback_model = "claude-haiku-4-5-20251001"

[api_keys]
anthropic = ""                              # set by user, never committed to git
openai = ""

[voice]
wake_phrase = "hey spaiOS"
push_to_talk_key = "super+shift+space"
```

The Orchestrator checks config on startup. Anthropic/OpenAI providers use their respective Python SDKs with the same message format as Ollama. Model switching is transparent to all agents.

---

## Session Breakdown

### Milestone 1: Voice Pipeline (Sessions 1–4)
- Session 1: `faster-whisper` install + test transcription quality with recorded clips
- Session 2: Microphone input loop — record on hotkey press, transcribe, inject to Orchestrator
- Session 3: Wake word detection with vosk (offline) — always-on listener in background thread
- Session 4: Full voice flow end-to-end: wake word → record → transcribe → response in overlay

### Milestone 2: Chrome App Control (Sessions 5–8)
- Session 5: Launch Chrome with debug port, connect CDP via websockets, verify connection
- Session 6: `open_url`, `get_current_url`, `get_page_content` working
- Session 7: `click_element`, `fill_input` — test age-gate scenario
- Session 8: Full Browser Agent with all tools, routing logic in Orchestrator

### Milestone 3: System-wide Input (Sessions 9–10)
- Session 9: ydotoold daemon setup, `type_text` and `click_at` via subprocess
- Session 10: AT-SPI element location → coordinate mapping → ydotool click

### Milestone 4: Persistent Memory (Sessions 11–13)
- Session 11: ChromaDB setup, `nomic-embed-text` via Ollama, store + retrieve test
- Session 12: Session log — auto-summarize on overlay close, load on open
- Session 13: User profile, context snippets, injection into system prompt

### Milestone 5: Remaining Agents + Config (Sessions 14–17)
- Session 14: Code Agent — read, write (with diff confirmation), run terminal command
- Session 15: Media Agent — "90s film" filter working end-to-end
- Session 16: MCP config system — switch between Ollama and Anthropic API via `config.toml`
- Session 17: "First Five" PRD scenarios all running end-to-end

### Milestone 6: Phase 2 Wrap (Sessions 18–20)
- Session 18–19: Full acceptance criteria test. Fix failures.
- Session 20: Retrospective, update Notion, write Phase 3 task breakdown.

---

## Acceptance Criteria

1. "hey spaiOS, open youtube.com" → Chrome opens/navigates to YouTube (no keyboard)
2. "search for lo-fi beats on YouTube" → Chrome searches without keyboard input
3. Age-gate page open in Chrome → "confirm I'm above 18" → AI clicks correct button
4. "what have I been working on?" → AI accurately recalls last 3 sessions from ChromaDB
5. "make this photo look like a 90s film" with image path → filter applied, output saved
6. "set up a workspace for the Tokyo project" → creates folder + blank file + opens editor
7. All Phase 1 acceptance criteria still pass with the new voice input path
8. Switch `config.toml` provider to "anthropic" + valid API key → Orchestrator uses Claude API
