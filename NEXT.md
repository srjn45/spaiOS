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

**Steps (M1 start):**
1. Create `compositor/` Rust crate: `cargo new --lib compositor`
2. Add Smithay dependency (latest stable), verify it compiles
3. Copy + run Smithay's `smallvil` example — make sure a window can be composited
4. Read `smallvil` code and annotate key concepts in a task doc
5. Scaffold `SpaiCompositor` struct replacing `smallvil` boilerplate
6. Milestone done when: blank Wayland compositor window appears on screen, a test Wayland client
   (e.g. `weston-terminal`) opens inside it

---

## How to update this file

At the end of each session, replace the "Current" block with the next milestone/session goal.
Format: milestone name, session number, ordered steps, Notion task link.
