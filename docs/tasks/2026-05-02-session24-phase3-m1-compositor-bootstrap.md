# Task: Phase 3 M1 — Compositor Bootstrap

**Date:** 2026-05-02
**Phase:** Phase 3 — The Shell
**Session goal:** Scaffold the `compositor/` Rust crate, add Smithay, and get a bare Wayland
compositor that opens a display so a Wayland client (e.g. `weston-terminal`) can connect to it.
**Notion task ID:** phase3_m1_compositor_foundation

## What We're Building

A minimal Smithay-based Wayland compositor crate at `compositor/`. This is the heart of Phase 3 —
it will eventually own the display, render the Neural Sphere natively in wgpu/WGSL, and manage all
app windows. This session: just get the skeleton running; visual output comes next session.

## Approach

1. Install Rust toolchain (rustup) and system Wayland/DRM dev libraries
2. `cargo new --lib compositor` inside the repo root
3. Add Smithay + dependencies to `Cargo.toml`
4. Implement `SpaiCompositor` that initialises a Wayland socket and event loop
5. Handle `wl_compositor` and `xdg_wm_base` globals so clients can connect
6. Render client surfaces to a winit window (easier than DRM/KMS for bootstrapping)
7. Run `weston-terminal` against the socket and verify it appears
8. Commit working scaffold

## Files Touched

- `compositor/Cargo.toml` — crate manifest + Smithay deps
- `compositor/src/lib.rs` — SpaiCompositor struct
- `compositor/src/main.rs` — entry point
- `compositor/src/state.rs` — Smithay compositor state (CalloopData)

## Done When

- [ ] `cargo build` succeeds with Smithay linked
- [ ] `cargo run` opens a Wayland compositor (winit window or headless socket)
- [ ] `WAYLAND_DISPLAY=wayland-1 weston-terminal` connects and shows a terminal window
