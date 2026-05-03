# spaiOS — Master Design Specification

> **One-line:** An AI-native operating system that replaces the App+File mental model with Intent+Agent — users describe goals, the OS handles execution.

**Date:** 2026-04-26 | **Version:** 1.0 | **Author:** Srajan Pathak

---

## ⚠ Direction Update (2026-05-03)

**Phase 3 has pivoted.** The custom Wayland compositor (original Phase 3) is parked. The new Phase 3 builds an AI assistant layer that works on top of any existing X11 Linux desktop by connecting the spaiOS overlay to the spaiSH daemon.

**Read first for current direction:**
- New Phase 3: `docs/phases/2026-05-03-phase-3-the-assistant-layer.md`
- Pivot design spec: `docs/superpowers/specs/2026-05-03-pivot-ai-assistant-design.md`

The original architecture and long-term vision below remain valid for Phase 4+.

---

## Quick Context (Read First — New Claude Session)

- **Project:** spaiOS — AI-native OS. Not yet an OS; currently in Phase 1 (Python overlay).
- **Developer:** Srajan Pathak (solo), 2 hrs/day, Claude as co-developer on all implementation.
- **Dev Machine:** HP Omen — i7-7700HQ, 16GB RAM, GTX 1050 Ti Mobile (4GB VRAM), Ubuntu 24.04 LTS.
- **Repo:** `/home/srajan/Development/spaiOS`
- **Current Phase:** Check `docs/phases/` for the active phase doc. Read it before starting any session.
- **Model Config:** Llama 3.2 3B via Ollama (fits 4GB VRAM). Do NOT use Llama 3.1 8B (too slow on CPU).
- **Interaction:** `Super+Space` → Neural Sphere overlay. Voice ("hey spaiOS") = Phase 2.
- **NVIDIA fix required:** Driver mismatch present (`NVML library 535.288`). Run `sudo ubuntu-drivers autoinstall && sudo reboot` before Session 1.

---

## Vision

spaiOS transitions computing from the **"Application + File"** paradigm to the **"Intent + Agent"** model.

In the App+File model, users manage tools and storage. They open Chrome to browse, VS Code to code, Finder to manage files — and they orchestrate everything themselves. The OS is a dumb launcher.

In the Intent+Agent model, users describe outcomes. "Research Tokyo restaurants and save the best ones." The OS decomposes this, dispatches agents, and returns a result. The OS is an intelligent partner.

The interface is a **Neural Sphere** — a pulsating, AI-powered overlay summoned at any moment on top of any app. It can see what the user sees, understand the context of any running application, ask clarifying questions, and take action on the user's behalf.

Eventually, the Neural Sphere *is* the OS — no traditional desktop, no file manager, no application launcher. Just intent and execution.

---

## Core Philosophy

1. **Intent over Syntax** — Users describe outcomes in natural language. The OS handles the how.
2. **Proactive Assistance** — Lightweight background Watchers anticipate needs before the user asks.
3. **Generative UI** — Interfaces are assembled dynamically based on active intent. No static desktop.
4. **Local-First & Private** — All AI processing on-device by default. Cloud is strictly opt-in.

---

## Architecture

### The Three AI Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER SPACE                             │
│                                                                 │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ Resource         │  │ Context        │  │ App Control    │  │
│  │ Governor         │  │ Watcher        │  │ Agent          │  │
│  │                  │  │                │  │                │  │
│  │ Predicts and     │  │ Passively      │  │ Actively acts  │  │
│  │ manages CPU /    │  │ monitors       │  │ inside running │  │
│  │ GPU / memory     │  │ screen, apps,  │  │ apps (click,   │  │
│  │ allocation       │  │ user context   │  │ type, navigate)│  │
│  └────────┬─────────┘  └──────┬─────────┘  └───────┬────────┘  │
│           │                   │                     │           │
└───────────┼───────────────────┼─────────────────────┼───────────┘
            │                   │                     │
┌───────────▼───────────────────▼─────────────────────▼───────────┐
│  KERNEL INTERFACES                                               │
│  eBPF probes + cgroups v2 + ghOSt    /proc + Wayland events     │
│  (Phase 4)                            AT-SPI + CDP + ydotool    │
└──────────────────────────────────────────────────────────────────┘
```

**Resource Governor (Phase 4):** User-space AI reads eBPF telemetry → manipulates cgroups/ghOSt. AI never runs in kernel-space — it loads small eBPF observation programs and acts on their output via safe kernel interfaces.

**Context Watcher (Phase 1+):** Background process monitoring active window, screen content, user activity. Feeds context to Orchestrator on every query. Passively observes, never acts autonomously.

**App Control Agent (Phase 2+):** Active actor inside running apps. AT-SPI for accessibility tree, Chrome DevTools Protocol (CDP) for deep browser control, ydotool for system-wide input simulation. Only acts on explicit user request.

### The Orchestrator

Central decision-maker powered by a local LLM (Llama 3.2 3B via Ollama). Receives user intent + screen context → routes to agents → manages multi-turn conversation → formats output for Neural Sphere.

### The Neural Sphere

Primary user interface. Phase 1: PyQt6 floating overlay with QPainter animation. Phase 3: Rust Wayland compositor shell (Smithay + wgpu). Three states: Idle (slow pulse), Thinking (node flicker), Acting (morphs into Generative UI cards).

---

## Phase Summary

| Phase | Name | Timeline | Deliverable |
|-------|------|----------|-------------|
| **1** | The Spark | Weeks 1–6 | Python overlay on Ubuntu: Neural Sphere, text input, screen awareness, file agent, error diagnosis |
| **2** | The Reach | Weeks 6–16 | Voice activation, Chrome app control, persistent memory, all PRD "First Five" scenarios |
| **3** | The Shell | Month 4–8 | Bootable Alpine distro, Rust Wayland compositor, Generative UI engine, Neural Sphere IS the desktop |
| **4** | The Nervous System | Month 8–18 | eBPF telemetry, Neural Scheduler, cgroups v2 + ghOSt, ARM (Raspberry Pi) |

### Product Evolution

```
Phase 1–2   →   spaiOS Overlay   →   Install on any Linux (pip install / shell script)
Phase 3+    →   spaiOS OS        →   Boot from USB, Neural Sphere is the entire desktop
```

Phase 1–2 code is NOT thrown away at Phase 3. Python services become systemd units inside the distro. The intelligence layer evolves; only the rendering surface changes.

---

## Technology Stack

| Component | Phase | Language | Library | Rationale |
|-----------|-------|----------|---------|-----------|
| Overlay UI | 1–2 | Python | PyQt6 | Custom painting (QPainter) for sphere animation, frameless windows |
| Orchestrator | 1+ | Python | ollama SDK | Native Python SDK, entire ML ecosystem is Python-first |
| Screen capture | 1+ | Python | Pillow + scrot | Simple, reliable, scrot is Wayland-compatible |
| App context | 1+ | Python | pyatspi | Linux AT-SPI Python bindings |
| Global hotkey | 1+ | Python | pynput | Cross-desktop keyboard listener |
| Voice STT | 2+ | Python | faster-whisper | Local Whisper, runs on CPU, ~150ms base model |
| Browser control | 2+ | Python | websockets (CDP) | Chrome DevTools Protocol, deep browser access |
| System-wide input | 2+ | System | ydotool | Wayland-compatible input simulation daemon |
| Persistent memory | 2+ | Python | ChromaDB | Embedded local vector DB, no separate server |
| Cloud model fallback | 2+ | Config | MCP | Model Context Protocol, user brings own API key |
| Wayland compositor | 3+ | Rust | Smithay | Best Wayland compositor lib, memory-safe |
| GPU rendering | 3+ | Rust | wgpu + WGSL | GPU shaders for Neural Sphere in compositor |
| eBPF probes | 4 | C | libbpf | BPF VM requires C; ecosystem standard |
| CPU scheduling | 4 | C/BPF | ghOSt | User-space scheduling via BPF |
| Resource limits | 4 | Python | cgroups v2 | Direct writes to /sys/fs/cgroup |

---

## Model Configuration (HP Omen — 4GB VRAM)

| Role | Model | VRAM | Speed |
|------|-------|------|-------|
| Orchestrator | `llama3.2:3b` | ~2.0GB | ~20 tok/sec on GPU |
| Vision | `moondream` | ~1.5GB | fast screen descriptions |
| Voice STT | `faster-whisper base` | 0 (CPU) | ~150ms per utterance |
| Embeddings | `nomic-embed-text` | ~0.6GB | fast, batch-able |
| **Total disk** | | ~5.5GB | 17GB free → comfortable |

**Hard constraint:** Do NOT pull `llama3.1:8b`. It requires 4.5GB VRAM, forces CPU inference at 5–8 tok/sec — too slow for a responsive overlay UX.

---

## Key Design Decisions

| Decision | Rationale | RFC |
|----------|-----------|-----|
| Option A: overlay before desktop replacement | Validates AI intelligence before compositor investment | RFC-005 |
| User-space AI governor, not kernel module | Safety: kernel-space crash = system panic. eBPF is sandboxed and verified | RFC-004 |
| Python first, Rust from Phase 3, C for eBPF only | Match language to actual performance need. AI layer doesn't benefit from Rust | RFC-002 |
| Llama 3.2 3B over Llama 3.1 8B | 4GB VRAM constraint. 3B on GPU >> 8B on CPU for latency | RFC-002 |
| 4-phase progressive build | Ship Phase 1–2 as standalone product while OS work happens | RFC-003 |
| MCP as AI bus | Swappable local/cloud models via config. User brings own API key | RFC-001 |

---

## Non-Goals

- **No custom kernel code** in Phase 1–3. eBPF in Phase 4 is loaded into kernel VM, not compiled into it.
- **No Windows/macOS support.** Linux-only. ARM comes in Phase 4.
- **No cloud dependency.** All Phase 1–2 features work fully offline.
- **No traditional app replacement** in Phase 1–2. Chrome, VS Code run normally.
- **No multi-user support** in MVP.

---

## Document Index

| Path | Purpose |
|------|---------|
| `docs/superpowers/specs/2026-04-26-spaiOS-design.md` | This file. Master design + quick session context. |
| `docs/phases/2026-04-26-phase-1-the-spark.md` | Phase 1: detailed spec, session breakdown, file structure, acceptance criteria |
| `docs/phases/2026-04-26-phase-2-the-reach.md` | Phase 2: voice, app control, memory, agents |
| `docs/phases/2026-04-26-phase-3-the-shell.md` | Phase 3: Wayland compositor, custom Alpine distro |
| `docs/phases/2026-04-26-phase-4-the-nervous-system.md` | Phase 4: eBPF, Neural Scheduler, Resource Governor |
| `docs/rfcs/2026-04-26-001-architecture.md` | Why Intent+Agent, the 3-layer architecture, alternatives |
| `docs/rfcs/2026-04-26-002-tech-stack.md` | Language choices, library choices, model choices |
| `docs/rfcs/2026-04-26-003-phase-structure.md` | Why 4 phases in this order |
| `docs/rfcs/2026-04-26-004-kernel-integration.md` | How AI interacts with kernel — eBPF, cgroups, ghOSt |
| `docs/rfcs/2026-04-26-005-interaction-model.md` | Overlay design, voice+text, Option A legacy compatibility |
| `docs/tasks/` | Per-session implementation plans. Created as work begins. |
