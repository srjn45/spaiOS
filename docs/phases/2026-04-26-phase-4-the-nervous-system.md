# Phase 4: The Nervous System

**Status:** Not started — begins after Phase 3 acceptance criteria pass
**Target:** Month 8–18 (~70–80 sessions × 2hrs)
**Output:** AI-driven resource management. eBPF telemetry, Neural Scheduler, cgroups/ghOSt, ARM support.

---

## Goal

spaiOS gains the ability to manage the machine's compute resources intelligently. The AI observes everything happening in the kernel, predicts what the user will need, and pre-allocates CPU/GPU/memory accordingly — making the machine feel faster without the user changing any settings.

**Showcase scenario:** Start a video export in a video editor. spaiOS detects the encode process starting, boosts its CPU priority via cgroups v2, throttles low-priority background processes, and the export completes measurably faster. The user didn't ask — the OS predicted and acted.

**ARM scenario:** spaiOS boots on a Raspberry Pi 4/5. Neural Sphere runs at 720p. All AI agents functional. Watchers active at low power draw.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                RESOURCE GOVERNOR (Python)               │
│                                                         │
│  Context: "user has been in video editor for 10 min"    │
│  Prediction: "encode process will start soon"           │
│  Decision: "pre-boost encoder cgroup, throttle sync"    │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
┌────────▼────────┐          ┌────────▼────────────┐
│  cgroups v2      │          │  ghOSt via BPF      │
│                  │          │                     │
│  CPU weight      │          │  Scheduling policy  │
│  Memory limit    │          │  Latency-sensitive  │
│  I/O weight      │          │  vs throughput      │
└────────▲────────┘          └────────▲────────────┘
         │                            │
┌────────┴────────────────────────────┴───────────────────┐
│                  eBPF PROBES (C)                         │
│                                                         │
│  sched_switch       block_rq_issue      mm_page_alloc   │
│  (who gets CPU)     (I/O wait)          (memory)        │
│                                                         │
│  thermal_zone       GPU utilization     net_dev_xmit    │
│  (/sys/class)       (NVML / sysfs)      (network I/O)   │
└─────────────────────────────────────────────────────────┘
```

The AI never runs in the kernel. It runs in user-space alongside the kernel, observing via eBPF and actuating via cgroups/ghOSt interfaces.

---

## Components

### 1. eBPF Telemetry Probes (`ebpf/`)

Small C programs (~50–200 lines each) compiled to BPF bytecode and loaded by the Resource Governor at startup via `libbpf`.

**Probe 1 — CPU Scheduler Events (`ebpf/sched_monitor.c`):**
```c
SEC("tp/sched/sched_switch")
int trace_sched_switch(struct trace_event_raw_sched_switch *ctx) {
    // Record: prev_pid, next_pid, prev_state, timestamp
    // Emit via ring buffer to user-space
}
```

**Probe 2 — Memory Pressure (`ebpf/mem_monitor.c`):**
```c
SEC("kprobe/try_charge_memcg")
int trace_memory_charge(struct pt_regs *ctx) {
    // Record: pid, bytes_requested, cgroup
}
```

**Probe 3 — I/O Wait (`ebpf/io_monitor.c`):**
```c
SEC("tp/block/block_rq_issue")
int trace_io_request(struct bpf_raw_tracepoint_args *ctx) {
    // Record: pid, device, bytes, timestamp
}
```

**Python reader (`src/core/ebpf_reader.py`):**
Loads eBPF probes via `bcc` Python library. Reads ring buffer continuously. Emits structured telemetry events to Resource Governor.

```python
# install: pip install bcc (requires kernel headers)
from bcc import BPF
b = BPF(src_file="ebpf/sched_monitor.c")
b.attach_tracepoint(tp="sched:sched_switch", fn_name="trace_sched_switch")
```

### 2. Resource Governor (`src/core/resource_governor.py`)

Python process that:
1. Reads eBPF telemetry stream (CPU, memory, I/O per process)
2. Reads Context Watcher (what user is doing right now)
3. Builds a real-time picture of system load by process
4. Predicts resource needs using rule-based model (Phase 4.0) → ML model (Phase 4.1)
5. Applies decisions via cgroups/ghOSt

**Prediction rules (Phase 4.0):**
```python
if context.app == "kdenlive" and cpu_trend(pid="ffmpeg", window=30s) == "rising":
    action = boost_cpu(pid="ffmpeg", shares=800)

if context.query_type == "compilation" and cpu_load > 80%:
    action = throttle_background_processes(except=["cc1", "ld", "make"])

if thermal_temp > 85:
    action = reduce_all_except_focused_app(reduction_pct=30)
```

**Actuation methods:**

```python
# cgroups v2 — direct writes to /sys/fs/cgroup
def set_cpu_weight(pid: int, weight: int):   # 1–10000, default 100
    path = f"/sys/fs/cgroup/spai/{pid}/cpu.weight"
    Path(path).write_text(str(weight))

def set_memory_max(pid: int, limit_mb: int):
    path = f"/sys/fs/cgroup/spai/{pid}/memory.max"
    Path(path).write_text(str(limit_mb * 1024 * 1024))

# cpufreq governor
def set_cpu_governor(governor: str):         # "performance" | "schedutil" | "powersave"
    for cpu in range(num_cpus):
        Path(f"/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor").write_text(governor)
```

### 3. ghOSt Integration (`ebpf/ghost_policy.c`)

ghOSt allows user-space programs to implement custom CPU scheduling via BPF. Requires Linux 5.15+ with `CONFIG_SCHED_CLASS_EXT=y`.

**Scheduling policies:**
- `LATENCY` — for interactive processes (compositor, voice listener). Minimize time from runnable to running.
- `THROUGHPUT` — for batch processes (video encode, compilation). Maximize CPU time when CPU available.
- `BACKGROUND` — for low-priority processes (sync, indexing). Only run when other processes idle.

The Resource Governor assigns policies based on process type and current user context.

### 4. Thermal Management (`src/core/thermal.py`)

```python
def read_temps() -> dict:
    # reads /sys/class/thermal/thermal_zone*/temp
    return {"cpu": 72, "gpu": 68}

def thermal_watch_loop():
    while True:
        temps = read_temps()
        if temps["cpu"] > THROTTLE_THRESHOLD:
            resource_governor.throttle_non_critical()
            if temps["cpu"] > WARN_THRESHOLD:
                neural_sphere.notify("Running hot — throttling background tasks")
        sleep(5)
```

### 5. "Vibe" Mode Resource Profiles

Vibe modes now have resource implications beyond just which services run:

**Quiet Mode:**
- Watcher services stopped
- `schedutil` CPU governor (kernel-managed, adaptive)
- eBPF probes not loaded
- Minimum resource footprint

**Partner Mode (default):**
- Watcher on 60s interval
- `schedutil` governor
- Basic eBPF telemetry (sched + memory only)
- Rule-based resource predictions

**Jarvis Mode:**
- Watcher continuous
- `performance` governor when plugged in, `schedutil` on battery
- All eBPF probes loaded
- Predictive pre-allocation active
- Loads model weights for predicted next task into GPU memory

### 6. ARM Support (Raspberry Pi 4/5)

**Kernel config additions for ARM64:**
```
CONFIG_BPF_JIT=y               # ARM64 BPF JIT for eBPF performance
CONFIG_SCHED_CLASS_EXT=y       # ghOSt support
```

**Model quantization for ARM:** Use `Q4_0` quantization (simpler, less memory) instead of `Q4_K_M`. Trade quality for speed on slower ARM CPU.

**GPU limitations:** Pi 4 has VideoCore VI GPU. wgpu Vulkan may not be available — fall back to GLES backend for Neural Sphere compositor. Resolution: 1080p (Pi 4) or 4K (Pi 5 with good cooling).

**Target:** Pi 5 (4x Cortex-A76 cores, 8GB RAM recommended). Pi 4 (4GB) is minimum.

---

## Session Breakdown (Milestones)

### Milestone 1: eBPF Foundations (~10 sessions)
- Learn eBPF fundamentals: "Learning eBPF" (Liz Rice, O'Reilly) — read alongside building
- Hello-world eBPF probe: trace any syscall, read output in Python via bcc
- Scheduler trace probe: record sched_switch events, stream to Python
- Verify on spaiOS distro with custom kernel flags enabled

### Milestone 2: Telemetry Pipeline (~8 sessions)
- All three probes (sched, memory, I/O) running simultaneously
- Ring buffer → Python reader → structured telemetry dict
- Real-time process CPU/memory/IO snapshot working
- Dashboard: show live telemetry in Neural Sphere (dev tool)

### Milestone 3: cgroups Actuation (~8 sessions)
- Create spaiOS cgroup hierarchy at boot
- Assign running processes to cgroups dynamically
- `set_cpu_weight` / `set_memory_max` working
- Measurable effect: boost a compile process, verify CPU priority via `systemd-cgtop`

### Milestone 4: ghOSt Integration (~10 sessions)
- Compile ghOSt on spaiOS Alpine fork (kernel must have `CONFIG_SCHED_CLASS_EXT`)
- Implement basic scheduling policy: LATENCY for compositor, THROUGHPUT for batch
- Resource Governor assigns policies based on process type
- Benchmark: measure scheduling latency improvement for compositor

### Milestone 5: Neural Scheduler (~10 sessions)
- Rule-based prediction model: process type → resource profile
- Real-time context integration: what user is doing → what resources they need
- Full prediction + actuation loop running
- Vibe mode resource profiles active

### Milestone 6: Thermal Management (~5 sessions)
- Thermal monitoring loop
- Throttle non-critical on high temp
- Neural Sphere notification for sustained throttling
- Recovery: restore normal resource allocation when temp drops

### Milestone 7: ARM / Raspberry Pi (~10 sessions)
- Cross-compile kernel with ARM64 BPF support
- Cross-compile compositor for ARM64
- Test boot on Pi 5
- Tune model quantization and GPU backend for Pi

### Milestone 8: Benchmarks + Polish (~8 sessions)
- Benchmark suite: measure export time, compile time with/without Neural Scheduler
- Document performance improvements
- Phase 4 acceptance criteria test
- Final docs update

---

## Prerequisites (Learn While Building)

| Topic | Resource |
|-------|----------|
| eBPF fundamentals | "Learning eBPF" — Liz Rice (O'Reilly, free online) |
| cgroups v2 | Linux kernel docs + `man 7 cgroups` |
| ghOSt | Google Research repo README + design doc |
| ARM cross-compilation | Alpine Linux ARM build guide |

---

## Acceptance Criteria

1. `cat /sys/fs/cgroup/spai/ffmpeg/cpu.weight` during video export → shows boosted weight (≥400 vs default 100)
2. Switch to "quiet mode" → `systemctl status spai-watcher` shows inactive
3. Switch to "jarvis mode" → `systemctl status spai-watcher` shows active, CPU governor = "performance" when plugged in
4. CPU temp > 85°C (simulate with stress) → Neural Sphere shows thermal notification within 10s
5. Benchmark: large C++ compile with Jarvis mode vs no spaiOS → ≥10% faster (measured via `time make`)
6. spaiOS boots on Raspberry Pi 5 → Neural Sphere appears, all Phase 2 features functional
