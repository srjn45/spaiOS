# Phase 1: The Spark

**Status:** Complete ✓
**Completed:** 2026-04-27 (Session 16 — 16 sessions, ~32hrs)
**Target:** Weeks 1–6 (~21 sessions × 2hrs = ~42hrs)
**Output:** pip-installable Python overlay app on Ubuntu

---

## Goal

A floating, screen-aware AI overlay on Ubuntu that can be summoned with `Super+Space`, see what is on the user's screen, understand the context of any running application, hold a multi-turn conversation, and manage files via natural language.

**The showcase scenario:** User has a Python file with an error open in VS Code. Presses `Super+Space`. Types "I'm getting an error, help me." spaiOS reads the screen, identifies the error on the correct line, explains it, and offers to fix it.

---

## Architecture

All components run inside a single Python process.

```
┌──────────────────────────────────────────────────────────────┐
│  spaiOS Overlay Process (src/main.py)                        │
│                                                              │
│  ┌─────────────────────┐     ┌──────────────────────────┐   │
│  │  Neural Sphere UI   │◄───►│  Orchestrator            │   │
│  │  (PyQt6)            │     │  (Ollama llama3.2:3b)    │   │
│  │                     │     │                          │   │
│  │  - frameless window │     │  - system prompt         │   │
│  │  - sphere animation │     │  - conversation history  │   │
│  │  - text input       │     │  - tool routing          │   │
│  │  - response display │     └──────────┬───────────────┘   │
│  └─────────────────────┘                │                   │
│                              ┌──────────┴──────────┐        │
│                              │                     │        │
│              ┌───────────────▼──────┐  ┌───────────▼──────┐ │
│              │  Context Capture     │  │  File Agent      │ │
│              │  - screenshot        │  │  - list_dir      │ │
│              │  - AT-SPI tree       │  │  - organize      │ │
│              │  - active window     │  │  - move/rename   │ │
│              └──────────────────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Neural Sphere Overlay (`src/ui/overlay.py`)

A frameless, always-on-top PyQt6 window. Summoned by `Super+Space`, dismissed by `Esc` or clicking outside.

**Window config:**
- Flags: `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`
- Background: `Qt.WA_TranslucentBackground` — see-through between elements
- Size: 480×420px, centered on primary screen
- Position: updated on each activation in case display config changed

**Layout:**
```
┌──────────────────────────────┐
│                              │
│       [Neural Sphere]        │  ← custom QPainter widget (200×200px)
│                              │
│  ┌────────────────────────┐  │
│  │  AI response text...   │  │  ← QTextEdit, read-only, auto-scroll
│  └────────────────────────┘  │
│  ┌─────────────────────┐[↵]  │
│  │  Ask anything...    │     │  ← QLineEdit + QPushButton
│  └─────────────────────┘     │
└──────────────────────────────┘
```

**Neural Sphere animation states:**
- **Idle:** Single circle, scale oscillates 0.95→1.05, opacity 0.6→0.8. Timer: 50ms tick.
- **Thinking:** 8 small satellite nodes orbit the center, random flicker on/off. Outer ring pulses faster.
- **Responding:** Nodes converge to center smoothly. Ease-in animation.

### 2. Orchestrator (`src/core/orchestrator.py`)

Manages the Ollama connection, conversation state, and tool routing.

**System prompt structure:**
```
You are spaiOS — an AI operating system assistant running on the user's Linux machine.
You can see the user's screen and help with anything they are doing right now.

Current context:
- Active application: {app_name}
- Window title: {window_title}
- Screen content: {visible_text}
- Screenshot: [attached image]

Rules:
- Be concise. One to three sentences unless detail is asked for.
- If you need to take a file action, use the available tools.
- If you are unsure what the user wants, ask ONE clarifying question.
- Never take destructive actions (delete, overwrite) without explicit confirmation.
```

**Conversation state:** List of `{"role": "user"|"assistant", "content": str}` dicts. Keep last 10 turns in memory. Reset on overlay close.

**Tool definitions (Ollama function calling):**
- `organize_folder(path: str)` → File Agent
- `list_files(path: str)` → File Agent
- `move_file(src: str, dst: str)` → File Agent
- `ask_clarification(question: str)` → renders in overlay, returns user response

**On each user message:**
1. Call `context.capture()` → get screenshot + AT-SPI tree
2. Build messages list with context injected into system prompt
3. Call Ollama with tools enabled
4. If tool call → execute tool → feed result back → get final response
5. Display response, update conversation history

### 3. Context Capture (`src/core/context.py`)

Grabs screen state on every query. Returns a single structured dict.

**Screenshot:** `subprocess.run(["scrot", "-z", "/tmp/spai_screen.png"])` → `PIL.Image.open()` → base64 encode for moondream vision model.

**AT-SPI tree:** `pyatspi.Registry.getDesktop(0)` → walk to focused window → collect text from labels, edit fields, status bars, error messages. Max 2000 chars to keep context window manageable.

**Window info:** `subprocess.run(["xdotool", "getactivewindow", "getwindowname"])` for window title + app name.

**Output:**
```python
{
  "app_name": "code",
  "window_title": "main.py — Visual Studio Code",
  "visible_text": ["def divide(a, b):", "    return a / b", "ZeroDivisionError: ..."],
  "screenshot_b64": "iVBORw0KGgo..."
}
```

### 4. File Agent (`src/agents/file_agent.py`)

Natural language file management. Operates only on `~/spaiOS-sandbox/` by default. User must explicitly approve any path outside the sandbox.

**Tools:**
```python
list_directory(path: str) -> dict          # files with sizes, types, modified dates
create_folder(path: str, name: str) -> str
move_file(src: str, dst: str) -> bool
rename_file(path: str, new_name: str) -> bool
delete_file(path: str) -> bool             # ALWAYS asks confirmation first
read_file_summary(path: str) -> str        # first 500 chars
```

**Organize flow:**
1. AI calls `list_directory` → sees all files
2. AI proposes categories in text response → user confirms
3. AI calls `create_folder` for each category → then `move_file` for each file

**Safety rules:**
- All paths validated: must resolve under approved base path
- `delete_file` → renders "Are you sure? This cannot be undone." in overlay
- System paths (`/etc`, `/usr`, `/bin`, `/boot`) hard-blocked regardless of user input

---

## Session Breakdown

### Milestone 1: Environment Setup (Sessions 1–2)

**Session 1 goal:** GPU inference working via Ollama.
- Fix NVIDIA driver: `sudo ubuntu-drivers autoinstall && sudo reboot`
- Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
- Pull models: `ollama pull llama3.2:3b && ollama pull moondream`
- Verify GPU: run `nvidia-smi` during `ollama run llama3.2:3b` — check GPU memory usage
- Test moondream: pass a screenshot, verify it describes the image

**Session 2 goal:** Python project skeleton with working Ollama call.
- Create virtualenv, `requirements.txt`, project folders
- Test `ollama` Python SDK: one-shot prompt → verify response
- Test vision: pass screenshot to moondream via SDK → get description
- Setup `sandbox/` folder with test files for File Agent later

### Milestone 2: The Overlay (Sessions 3–5)

**Session 3 goal:** Frameless overlay window activates on `Super+Space`.
- PyQt6 frameless window with transparent background
- Global hotkey via `pynput.keyboard.GlobalHotKeys` in background thread
- Window appears centered, dismisses on `Esc`
- No AI yet — just the window shell

**Session 4 goal:** Neural Sphere animation working in the overlay.
- Custom `NeuralSphere` widget using QPainter
- Idle state: slow pulsing circle
- Thinking state: orbiting nodes with random flicker (triggered manually for now)
- QTimer driving animation at 50ms

**Session 5 goal:** Text input + Ollama response displayed in overlay.
- `QLineEdit` for input, `QTextEdit` for response
- On Enter: hardcoded system prompt → Ollama call → display response
- Thinking animation plays while awaiting Ollama response
- Basic end-to-end loop working

### Milestone 3: The Eyes (Sessions 6–7)

**Session 6 goal:** Screenshot capture and vision working.
- `scrot` screenshot on each query → Pillow load → base64
- Pass to moondream via Ollama → get screen description
- Vision description injected into Orchestrator system prompt

**Session 7 goal:** AT-SPI + window info working.
- `pyatspi` reads focused app accessibility tree → visible text extracted
- `xdotool` gets active window title and app name
- Context dict assembled and injected into system prompt
- Test: VS Code with Python file open → verify AI sees the code

### Milestone 4: The Brain (Sessions 8–11)

**Session 8 goal:** Proper Orchestrator with function calling.
- Structured system prompt with context injection
- Conversation history (last 10 turns)
- Ollama function calling enabled with File Agent tools defined

**Session 9 goal:** Context-aware, multi-turn conversation.
- AI references visible screen content in responses
- Follow-up questions work: user can respond to AI questions
- Test: error in VS Code → two-turn conversation about the fix

**Session 10 goal:** Clarifying questions flow.
- AI can ask a clarifying question mid-task
- Overlay stays open, user answers, AI continues
- UI clearly indicates "AI is asking" vs "AI is responding"

**Session 11 goal:** Loading states and error handling.
- Thinking animation plays while Ollama is processing
- Ollama errors (model not found, server down) show friendly message in overlay
- Long responses truncate gracefully with "show more" option

### Milestone 5: File Agent (Sessions 12–15)

**Session 12 goal:** File Agent tools working standalone.
- All tool functions implemented and tested in Python directly
- `sandbox/` folder has 20+ messy test files (mixed types, no organization)
- `list_directory`, `create_folder`, `move_file`, `delete_file` all functional

**Session 13 goal:** Orchestrator routes to File Agent.
- "Organize my sandbox" → AI calls `list_directory` → proposes categories → asks confirmation
- User says yes → AI calls `create_folder` + `move_file` in sequence
- Confirmation flow for destructive ops renders in overlay

**Session 14 goal:** Safety mechanisms.
- Path validation prevents operations outside sandbox
- Delete confirmation always fires
- "Undo last action" basic support (move files back)

**Session 15 goal:** Error handling for File Agent.
- File not found, permission denied, path outside sandbox → friendly error in overlay
- Agent doesn't crash on unexpected file system state

### Milestone 6: The Demo + Polish (Sessions 16–19)

**Session 16–17 goal:** Error diagnosis showcase end-to-end.
- VS Code with broken Python file open
- `Super+Space` → "help with this error"
- AI reads screen via AT-SPI + screenshot → identifies error line → explains it
- AI offers to fix → user confirms → AI outputs corrected code to overlay
- This is the Phase 1 hero demo

**Session 18 goal:** Visual polish.
- Overlay drop shadow
- Smoother animation transitions
- Markdown rendering in response area (bold, code blocks, bullet points)
- Subtle gradient background on overlay

**Session 19 goal:** Packaging.
- `pyproject.toml` with entry point: `spaiOS`
- `pip install .` from repo root installs and adds `spaiOS` command
- First-run wizard: checks Ollama running, checks models pulled, creates sandbox folder
- Desktop `.desktop` file for launcher integration

### Milestone 7: Phase 1 Wrap (Sessions 20–21)

**Session 20:** Run all 6 acceptance criteria. Fix any failures.

**Session 21:** Write session log in Notion. Draft Phase 2 task breakdown. Update master design doc if anything changed.

---

## Project Structure

```
spaiOS/
├── src/
│   ├── ui/
│   │   ├── overlay.py          # Main PyQt6 overlay window
│   │   ├── neural_sphere.py    # Animated sphere QPainter widget
│   │   └── components.py       # Response display, text input
│   ├── core/
│   │   ├── orchestrator.py     # Ollama orchestrator + conversation state
│   │   ├── context.py          # Screenshot + AT-SPI capture
│   │   └── hotkey.py           # Global Super+Space listener (pynput)
│   ├── agents/
│   │   └── file_agent.py       # File management tools
│   └── main.py                 # Entry point: init Qt app, start hotkey, run loop
├── sandbox/                    # Test folder for File Agent (populated with messy files)
├── docs/                       # All documentation
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Dependencies

`requirements.txt`:
```
PyQt6>=6.6.0
ollama>=0.2.0
pyatspi>=2.38.0
Pillow>=10.0.0
pynput>=1.7.6
python-xlib>=0.33
```

System packages:
```bash
sudo apt install scrot xdotool python3-atspi
```

---

## Acceptance Criteria

Phase 1 is done when all pass:

1. `Super+Space` → Neural Sphere overlay appears in under 500ms
2. Type "what app is open?" with any application focused → AI names the correct app
3. Open a Python file with a syntax error in VS Code → `Super+Space` → "help with this error" → AI identifies the error and explains it correctly
4. Type "organize my sandbox" → AI proposes categories → user confirms → files are moved correctly
5. Type "delete all files in sandbox" → AI asks "Are you sure?" before any deletion
6. `Esc` → overlay dismisses cleanly, no crash, re-opens immediately on `Super+Space`

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| NVIDIA driver mismatch → no GPU | Fix first (Session 1). Fallback: use CPU with llama3.2:3b (~8 tok/sec, borderline usable for demos). |
| AT-SPI not exposed by target app | Fall back to screenshot + moondream description. AT-SPI is bonus context, not required. |
| `Super+Space` conflicts with system shortcut | Test. Alternative: `Ctrl+Alt+Space`. Document reconfiguration. |
| Ollama model slow on first token | Show thinking animation immediately. First-token latency is ~500ms on GPU — acceptable. |
| PyQt6 overlay flicker on Wayland | Use `XDG_SESSION_TYPE=x11` for Phase 1 if needed. Pure Wayland overlay is Phase 3 work. |
