# RFC-003: Phase Structure — Why 4 Phases in This Order

**Date:** 2026-04-26
**Status:** Accepted
**Author:** Srajan Pathak

---

## The Four Phases

| Phase | Name | Duration | Key Output |
|-------|------|----------|------------|
| 1 | The Spark | Weeks 1–6 | Python overlay on Ubuntu, screen-aware AI, file agent |
| 2 | The Reach | Weeks 6–16 | Voice, Chrome app control, persistent memory, all agents |
| 3 | The Shell | Month 4–8 | Custom Alpine distro, Wayland compositor, Generative UI |
| 4 | The Nervous System | Month 8–18 | eBPF telemetry, Neural Scheduler, ARM support |

---

## Why This Order

### Validate intelligence before infrastructure

The core value of spaiOS is the AI intelligence layer — the Orchestrator's reasoning, the agents' capabilities, the context capture quality. None of this requires a custom OS.

If the Orchestrator gives poor responses or the AT-SPI integration is unreliable, no amount of Wayland polish or eBPF instrumentation fixes the product. Phase 1–2 exist to validate the intelligence layer on a real machine before any OS investment.

### Ship early, ship usably

A Python overlay on Ubuntu is installable in 5 minutes. A custom Linux distro requires burning a USB, repartitioning, and accepting installation risk. Starting with the overlay means:
- Something usable exists after 6 weeks
- Feedback loop before expensive work
- Early adopters can try it without wiping their OS

Phase 1–2 are a standalone product: "spaiOS Overlay — the AI that knows what's on your screen."

### User-facing impact before invisible optimizations

App control (Phase 2) is what makes spaiOS feel like Jarvis. Resource management (Phase 4) makes the machine faster but is invisible to the user. The impressive, visible capability comes first. The infrastructure optimization comes after, on a solid foundation.

### Custom distro before kernel integration

The Neural Scheduler (Phase 4) needs custom kernel compile flags (`CONFIG_SCHED_CLASS_EXT` for ghOSt, `CONFIG_BPF_JIT` for ARM). These flags require building our own kernel. We can't rely on Ubuntu's stock kernel for Phase 4 features. Phase 3 (building the custom distro) gives us kernel control before Phase 4 needs it.

---

## Phase Dependencies

```
Phase 1 (overlay)
    │  validates: screen capture, Orchestrator, file agent
    │
    └──► Phase 2 (app control + voice + memory)
             │  validates: app control, voice, memory, all agents
             │
             └──► Phase 3 (distro)
                      │  Python services → systemd services
                      │  overlay → Wayland compositor shell
                      │
                      └──► Phase 4 (kernel integration)
                               custom kernel config enabled in Phase 3
```

Each phase is a direct prerequisite for the next. No phase is a throwaway — code, architecture, and learnings all carry forward.

---

## Code Continuity

Phase 1–2 Python code becomes Phase 3 systemd services. Example:

| Phase 1–2 | Phase 3 |
|-----------|---------|
| `orchestrator.py` process | `spai-orchestrator.service` |
| watcher threads in main process | `spai-watcher.service` |
| file agent as function | `spai-file-agent` socket-activated service |
| ChromaDB embedded | `spai-memory.service` |

The intelligence layer (all Python) is unchanged. Only the service boundary and rendering surface change.

---

## Timeline Estimate (2hrs/day, solo)

| Phase | Sessions | Weeks | Cumulative |
|-------|----------|-------|------------|
| Phase 1 | ~21 | 1–6 | Month 1.5 |
| Phase 2 | ~22 | 6–16 | Month 4 |
| Phase 3 | ~50 | 16–40 | Month 10 |
| Phase 4 | ~75 | 40–78 | Month 18–20 |

These are estimates. Phase 3 and 4 timelines have high variance depending on Smithay and eBPF learning curve. Each phase ends when its acceptance criteria pass — not at a fixed date.
