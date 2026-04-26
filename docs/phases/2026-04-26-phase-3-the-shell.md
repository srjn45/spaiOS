# Phase 3: The Shell

**Status:** Not started — begins after Phase 2 acceptance criteria pass
**Target:** Month 4–8 (~45–60 sessions × 2hrs)
**Output:** Bootable Alpine Linux ISO with Neural Sphere as the complete desktop shell

---

## Goal

spaiOS becomes a real operating system. Boot from USB into spaiOS — no GNOME, no KDE, no traditional desktop. The Neural Sphere IS the shell. Traditional apps (Chrome, VS Code, terminal) run as Wayland clients inside the compositor.

**Showcase scenario:** Boot HP Omen from USB. Neural Sphere appears on a black screen. Press `Super+Space`. Type "open Chrome". Chrome launches as a Wayland window managed by the spaiOS compositor. All Phase 2 capabilities work natively.

---

## What Changes from Phase 1–2

The Phase 1–2 Python app is NOT rewritten — it is reorganized into systemd services running inside the custom distro. The intelligence layer is unchanged.

```
Phase 1–2 Python app               Phase 3 spaiOS distro
────────────────────────────────────────────────────────
Neural Sphere overlay (PyQt6)  →  Rust Wayland compositor shell
Orchestrator process           →  systemd: spai-orchestrator.service
Context Watcher threads        →  systemd: spai-watcher.service
App Control Agent              →  systemd: spai-app-control.service
ChromaDB memory                →  systemd: spai-memory.service
Voice listener                 →  systemd: spai-voice.service
```

Code path: Python services call into the Rust compositor via Unix domain socket for rendering commands. The compositor calls Python services for AI decisions.

---

## New Components

### 1. Wayland Compositor (`compositor/`)

**Language:** Rust
**Library:** Smithay (https://github.com/smithay/smithay)

The compositor is the heart of Phase 3. It owns the display, manages all windows, handles all input, and renders the Neural Sphere directly — no separate overlay process.

**Responsibilities:**
- Initialize DRM/KMS display pipeline (direct framebuffer access)
- Accept Wayland client connections (Chrome, VS Code, etc.)
- Position and composite client surfaces on screen
- Handle keyboard/mouse/touch input, route to focused client
- Render Neural Sphere natively (not as a Wayland client)
- Implement `wlr-layer-shell` for persistent overlay surfaces
- Run XWayland for legacy X11 app compatibility

**Compositor architecture:**
```
DRM/KMS (hardware display)
    ↑
Compositor render loop (wgpu)
    ├── Neural Sphere layer     ← always on top, rendered by compositor
    ├── Active client windows   ← Chrome, VS Code as Wayland surfaces
    └── Background layer        ← solid color or gradient
```

**IPC with Python services:**
Unix domain socket at `/run/spai/compositor.sock`. Python services send render commands:
```json
{"cmd": "set_sphere_state", "state": "thinking"}
{"cmd": "show_overlay", "content": "AI response text..."}
{"cmd": "hide_overlay"}
{"cmd": "show_ui_blueprint", "blueprint": {...}}
```

### 2. Neural Sphere in Rust (wgpu + WGSL)

Phase 3 replaces the QPainter sphere with GPU-rendered shaders. Visual quality improvement is significant.

**WGSL shader approach:**
- Sphere: signed distance function (SDF) with subsurface scattering approximation
- Idle pulse: sine wave driving emissive intensity
- Thinking: particle system — 64 nodes orbiting center with randomized speeds
- Acting: nodes collapse toward center, UI blueprint cards unfold from sphere

**wgpu integration:** Compositor uses wgpu for all rendering. Neural Sphere is one render pass.

### 3. Generative UI Engine (compositor + Python)

The Orchestrator outputs `UI_BLUEPRINT` JSON when it wants to show structured UI instead of plain text. The compositor parses blueprints and renders dynamic card layouts.

**Blueprint format:**
```json
{
  "type": "card_grid",
  "title": "Photo Gallery",
  "cards": [
    {
      "type": "image_preview",
      "path": "/home/srajan/Photos/tokyo.jpg",
      "label": "Tokyo Street",
      "actions": [{"label": "Apply 90s Filter", "tool": "media_filter"}]
    },
    {
      "type": "text_card",
      "content": "3 photos in this folder"
    }
  ]
}
```

**Card types for Phase 3:**
- `image_preview` — thumbnail + label + action buttons
- `text_card` — formatted text with optional markdown
- `file_list` — scrollable file listing with icons
- `action_buttons` — row of action buttons
- `input_card` — text input field for follow-up responses

### 4. Custom Alpine Base (`distro/`)

**Base:** Alpine Linux 3.20+ minimal (kernel + BusyBox + musl libc, ~8MB base)

**Kernel configuration (custom compile):**
```
CONFIG_BPF=y                    # eBPF support (needed for Phase 4)
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_CGROUP_BPF=y             # cgroups + BPF
CONFIG_DRM=y                    # Direct rendering for Wayland
CONFIG_DRM_I915=y               # Intel GPU support (HP Omen integrated)
CONFIG_DRM_NOUVEAU=y            # NVIDIA support
```

**Packages added:**
```
python3.11, py3-pip              # Python runtime
wayland-libs, mesa, libdrm       # Wayland stack
xwayland                         # Legacy X11 app support
systemd                          # Service management (replaces OpenRC)
ollama                           # AI model server
```

**Packages excluded:** X11 server, all desktop environments, pulseaudio (use pipewire), bluetooth stack (initially).

### 5. systemd Services

```
/etc/systemd/system/
├── spai-compositor.service    # Starts first. Owns display. Deps: DRM device ready.
├── spai-orchestrator.service  # After compositor. Main AI brain.
├── spai-watcher.service       # After orchestrator. Context monitoring.
├── spai-voice.service         # After orchestrator. Mic listener.
├── spai-app-control.service   # Socket-activated. On-demand.
└── spai-memory.service        # After network. ChromaDB + embeddings.
```

**Vibe modes as systemd targets:**
```
spai-quiet.target    # compositor + orchestrator only
spai-partner.target  # + watcher (default, auto-started at boot)
spai-jarvis.target   # + voice + continuous screen monitoring
```

User switches via: "hey spaiOS, switch to quiet mode" → Orchestrator calls `systemctl isolate spai-quiet.target`.

### 6. Installer

Shell script that runs from a live USB environment:
1. Detect target disk, confirm with user
2. Partition (EFI + root)
3. Extract Alpine base
4. Install spaiOS compositor binary + Python services
5. Run Ollama to pull models (`llama3.2:3b`, `moondream`, `nomic-embed-text`)
6. Configure systemd services for autostart
7. First-boot wizard: name, API keys (optional), WiFi config
8. Install GRUB bootloader

**Output:** Bootable system in ~15 minutes on a fast connection.

---

## Session Breakdown (Milestones)

### Milestone 1: Compositor Foundation (~15 sessions)

Learn Smithay and build the basic compositor:
- Display initialization via DRM/KMS
- Accept Wayland client connections
- Render client surfaces on screen
- Keyboard + mouse input routing to focused client
- Window focus management

Start from Smithay's `smallvil` example compositor. Understand it fully before modifying.

### Milestone 2: Neural Sphere in Rust (~8 sessions)

- wgpu initialization inside compositor
- Idle sphere: SDF circle with pulse animation in WGSL
- Thinking sphere: particle system
- IPC socket: receive state commands from Python
- Acting sphere: card unfold animation

### Milestone 3: Python Services as systemd (~5 sessions)

- Refactor Phase 2 code: separate each component into its own service module
- Write systemd unit files for each service
- Test service start/stop/restart
- Vibe mode targets working

### Milestone 4: Generative UI Engine (~8 sessions)

- Blueprint parser in Rust compositor
- `image_preview` card renderer
- `text_card` renderer with markdown-like formatting
- `file_list` renderer
- `action_buttons` → route button press back to Python via IPC

### Milestone 5: Alpine Distro Build (~8 sessions)

- Custom kernel config: compile Alpine kernel with BPF + DRM flags
- Package selection + build script (using Alpine's `abuild`)
- Systemd integration in Alpine (non-trivial — Alpine defaults to OpenRC)
- Boot sequence: kernel → systemd → spai-compositor

### Milestone 6: Installer + ISO (~6 sessions)

- Installer shell script
- Grub config
- First-boot wizard (Python TUI or Neural Sphere itself)
- Generate bootable ISO with `mkisofs`
- Test on HP Omen from USB

### Milestone 7: Integration + Polish (~5 sessions)

- All Phase 2 capabilities working inside new OS
- XWayland: verify Chrome and VS Code launch correctly
- Vibe mode switching working end-to-end
- Phase 3 acceptance criteria test

---

## Key Technical Challenges

**Smithay learning curve:** Wayland compositor development is complex. Budget 10–15 sessions for the compositor foundation. The Smithay docs are good but sparse. Start with `smallvil` (example compositor in Smithay repo) and build up.

**Alpine + systemd:** Alpine uses OpenRC by default. Adding systemd requires careful setup. Reference: `alpine-linux-systemd` community overlay or build from scratch.

**wgpu on GTX 1050 Ti:** NVIDIA requires Vulkan backend for wgpu. NVIDIA Vulkan driver must be installed. Alternatively, use OpenGL backend — more compatible but slightly slower.

**Python ↔ Rust IPC:** Keep the socket protocol simple and versioned. JSON over Unix domain sockets is fine for Phase 3. Protobufs if performance becomes an issue.

---

## Acceptance Criteria

1. Boot HP Omen from USB → Neural Sphere appears on black background, no traditional desktop
2. `Super+Space` → overlay activates, text input works, AI responds
3. "open Chrome" → Chrome launches as Wayland client, visible in compositor
4. "hey spaiOS, switch to quiet mode" → Watcher services stop, confirmed via `systemctl status`
5. All Phase 2 acceptance criteria pass in the new OS environment
6. Reboot → ChromaDB memory persists, user name remembered
7. VS Code opens and displays code correctly via XWayland
