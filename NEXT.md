# Next Session

This file always reflects the single next thing to work on.
Update it at the end of every session before committing.

---

## Current: Phase 3 — Milestone 1 (Compositor Foundation)

**Goal:** Bootstrap the Rust Wayland compositor. Get Smithay's `smallvil` example running, understand
it fully, then scaffold the spaiOS compositor crate.

**Notion task:** phase3_m1_compositor_foundation

**Done (Phase 2 complete — M7 smoke-test notes):**
- AC9 passed. AC10/AC11 deferred: root causes found, fixes applied (see
  docs/tasks/2026-05-02-session23-m7-smoke-test.md). Re-test when convenient.

**Done (Session 24):**
- `compositor/` crate created with Smithay 0.7, calloop 0.14, wayland-server 0.31
- `SpaiState` wires CompositorHandler + ShmHandler + SeatHandler + XdgShellHandler
- `ListeningSocket` on `WAYLAND_DISPLAY=wayland-spai`; calloop event loop running
- `cargo build` passes cleanly

**Steps (remaining for M1):**
1. Run `cargo run` in compositor/ and test: `WAYLAND_DISPLAY=wayland-spai weston-terminal`
2. Add `OutputManagerState` + a virtual output so clients configure correctly
3. Add `wl_seat` with keyboard — so `weston-terminal` can receive input
4. Add Winit backend window (render client surfaces into a host window for dev testing)
5. Milestone done when: `weston-terminal` opens inside the compositor window and accepts text

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
