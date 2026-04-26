# RFC-001: Core Architecture — Intent + Agent Model

**Date:** 2026-04-26
**Status:** Accepted
**Author:** Srajan Pathak

---

## Problem

Traditional operating systems require users to manage tools (applications), manage storage (files), and orchestrate their own workflows. This places the cognitive burden of "how" entirely on the user.

A user who wants to "research Tokyo restaurants and save the best ones" must: open a browser, search, copy content, open a notes app, paste, organize — a sequence of tool operations rather than a single intent. The OS is a dumb launcher.

---

## Proposal

Replace the App+File mental model with Intent+Agent:

- User expresses intent in natural language
- Orchestrator decomposes intent into agent tasks
- Specialized agents execute tasks (Browser Agent, File Agent, Code Agent)
- User receives outcome — not a sequence of tool operations

The interface is a single point of contact — the **Neural Sphere** — always available, always aware of what is on screen.

---

## Architecture Adopted

Three AI capability layers orchestrated by a central LLM:

**Orchestrator:** Routes intent to agents, maintains conversation state, powered by Llama 3.2 3B via Ollama (Phase 1–2) / local model in compositor (Phase 3+).

**Context Watcher:** Passively monitors active window, screen content, user activity. Feeds context to Orchestrator on every query. Never acts autonomously.

**App Control Agent:** Actively interacts with running applications on user's explicit request. AT-SPI for accessibility tree, Chrome DevTools Protocol for browser, ydotool for system-wide input.

**Resource Governor:** Predicts resource needs from context + eBPF telemetry. Allocates CPU/GPU/memory via cgroups v2 and ghOSt. Phase 4 work.

**Neural Sphere:** The single UI surface. Phase 1: PyQt6 overlay. Phase 3: Wayland compositor shell.

---

## Alternatives Considered

**Desktop replacement from day one:**
Build a completely custom UI from scratch, no traditional app support.
*Rejected:* Too high risk. Loses existing software ecosystem. No path to validation before massive investment.

**AI as a plugin on macOS/Windows:**
Wrap existing OS with AI capabilities as a third-party app.
*Rejected:* Platform-dependent. No path to the full OS vision. Can't control resource management.

**Overlay first, OS later (adopted):**
Start with Python overlay on existing Linux. Progressive transition to full OS over 4 phases.
*Adopted because:* Validates the AI intelligence layer before investing months in kernel/compositor work. Phase 1–2 ship as a standalone useful product.

---

## MCP as the AI Bus

Model Context Protocol (MCP) is adopted as the standard interface for AI model switching. Users can configure `config.toml` to switch between Ollama (local) and cloud providers (Anthropic, OpenAI). The Orchestrator is model-agnostic — it speaks the same tool-calling interface regardless of provider.

This makes spaiOS local-first with a clear, user-controlled cloud upgrade path.

---

## Consequences

- Phase 1–2 requires user to already have Linux installed
- Full OS experience is Phase 3+ (4+ months)
- The intelligence layer is validated before expensive infrastructure work
- MCP dependency: tool-calling format must be compatible across providers
