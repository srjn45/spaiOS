# RFC-005: Interaction Model — Overlay, Voice + Text, Legacy App Compatibility

**Date:** 2026-04-26
**Status:** Accepted
**Author:** Srajan Pathak

---

## The Neural Sphere as Overlay

**Decision:** In Phase 1–2, the Neural Sphere is a floating overlay summoned on top of any running application. It is not a desktop replacement. Traditional apps run normally underneath.

**Activation:** `Super+Space` keyboard shortcut (Phase 1). "Hey spaiOS" voice wake phrase (Phase 2). Both trigger the same overlay — voice activates with audio input focused, keyboard with text input focused.

**Why overlay first:** A desktop replacement requires Phase 3 (Wayland compositor, custom distro — 4+ months). An overlay runs today. The core AI intelligence is identical regardless of the rendering surface. Overlay first means the intelligence is validated and useful before the OS work begins.

**Phase 3 transition:** The overlay becomes the shell. The Neural Sphere animation, the conversation UX, and the AI brain are unchanged. The PyQt6 window is replaced by a native Wayland surface rendered directly by the compositor.

---

## Dual Input: Voice + Text

**Text input (Phase 1):** `Super+Space` → frameless overlay appears with `QLineEdit` focused. User types, presses Enter.

**Voice input (Phase 2):** "Hey spaiOS" wake phrase detected → overlay appears with mic indicator → user speaks → 1.5s silence ends utterance → faster-whisper transcribes → sent to Orchestrator.

**Push-to-talk fallback (Phase 2):** `Super+Shift+Space` — for environments where always-on microphone is unwanted. Holds mic open while key is held.

**Overlap handling:** If both keyboard shortcut and voice trigger simultaneously (rare), voice takes priority — the user clearly intended to speak.

---

## Legacy App Compatibility: Option A

Three options were evaluated for how spaiOS relates to traditional applications:

**Option A: AI overlay on traditional desktop (adopted for Phase 1–2)**
Traditional apps (Chrome, VS Code, Spotify) run exactly as they do on any Linux distro. Neural Sphere is an overlay. AI assists and controls apps via AT-SPI/CDP/ydotool but does not replace their UI.

*Adopted because:* Full backward compatibility with existing software ecosystem. Zero app porting required. Users keep their existing workflows while gaining AI assistance.

**Option B: Apps wrapped in Generative UI cards (Phase 3+ hybrid)**
Apps still run natively, but the compositor wraps their windows in AI-generated frames. The user sees AI-generated chrome around each app rather than traditional window decorations. Generative UI cards appear contextually alongside app windows.

*Planned for Phase 3:* The compositor design accommodates this. Not a Phase 1–2 goal.

**Option C: Clean break — no traditional apps (long-term north star)**
Everything is AI-mediated. No traditional application windows. Generative UI for every interaction.

*Not before Phase 5+:* Requires a complete Generative UI ecosystem capable of replacing every app the user needs. Realistically 2–3 years after Phase 3. The foundation built in Phases 1–4 enables this eventual transition.

**The product evolution story:**
```
Phase 1–2: "AI that helps with your desktop"
Phase 3:   "AI that is your desktop"
Phase 4+:  "Desktop that disappears"
```

---

## App Control: AI Hands on the Desktop

The interaction model includes the AI actively acting inside running applications when the user asks. This is the "computer use" layer — the AI has both eyes (Context Watcher) and hands (App Control Agent) on the entire desktop.

**Eyes:** Screenshot via scrot + AT-SPI accessibility tree for structured app state.

**Hands:**
- AT-SPI: programmatic interaction with accessible app elements (click, type, select)
- Chrome DevTools Protocol: deep browser automation (navigate, fill forms, click by selector)
- ydotool: input simulation for apps without accessibility support

**Privacy model:** The AI acts only on explicit user request. The Context Watcher passively observes but never triggers App Control autonomously. The user must ask for an action for the App Control Agent to do anything.

---

## Conversational Model

The Orchestrator maintains multi-turn conversation state for the duration of an overlay session (from activation to dismissal). This enables:

- AI asks one clarifying question before acting
- User can say "yes, do it" or "no, wait" in response
- Follow-up requests reference earlier turns ("do the same thing for the other file")
- Session memory via ChromaDB persists key context across sessions

**Conversation reset:** Overlay dismissal clears the in-session conversation history. Only the ChromaDB-persisted summary carries forward to the next session.
