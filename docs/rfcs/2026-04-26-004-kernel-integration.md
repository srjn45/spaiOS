# RFC-004: How AI Interacts with the Linux Kernel

**Date:** 2026-04-26
**Status:** Accepted
**Author:** Srajan Pathak

---

## The Question

"AI tied into the kernel" is the core spaiOS claim. This RFC defines precisely what that means — and what it does not mean.

---

## What We Do NOT Do

**No kernel modules:** C code loaded via `insmod` or `modprobe`. A bug in a kernel module causes a kernel panic (system crash). AI-driven code that can crash the OS is unacceptable. Not implemented at any phase.

**No kernel source modification:** We do not fork or patch the Linux kernel source code. The kernel used is standard Linux, possibly with custom compile-time configuration flags enabled, but no line of kernel C source is changed.

**No AI running in kernel-space:** An LLM running in kernel-space is both technically impossible (kernel has no libc, no dynamic allocation, no floating point by default) and architecturally wrong. A crash in kernel space = kernel panic = system reboot.

---

## What We DO (Phase 4)

Three kernel interaction mechanisms:

### Mechanism 1: eBPF Programs

Small C programs compiled to BPF bytecode and loaded into the kernel's BPF virtual machine. They observe kernel events and stream data to user-space via ring buffers.

**What makes eBPF safe:**
- The BPF verifier checks every program before loading. Unsafe programs are rejected.
- Programs have bounded loop iterations — they cannot infinite-loop in the kernel.
- They run in a sandboxed VM, not directly in kernel code.
- A buggy eBPF program is rejected at load time or terminated — it cannot crash the kernel.

```
C eBPF program (in kernel BPF VM)
    ├── observes: scheduler decisions every task switch
    ├── observes: memory allocation per process
    └── observes: I/O requests as they enter the block layer
         ↓ ring buffer
Python Resource Governor (user-space)
    ├── reads telemetry in real-time
    └── makes AI decisions about resource allocation
```

### Mechanism 2: cgroups v2

The Linux kernel's built-in resource management system. User-space programs write to `/sys/fs/cgroup/` filesystem to set per-process-group limits.

No custom kernel code. No eBPF needed. This is standard Linux administration, accessible since kernel 4.x.

```bash
# Set CPU weight for a process (higher = more CPU time)
echo 500 > /sys/fs/cgroup/spai/video-encoder/cpu.weight

# Set memory limit
echo $((4 * 1024 * 1024 * 1024)) > /sys/fs/cgroup/spai/browser/memory.max
```

The Resource Governor writes these values based on AI decisions. The kernel enforces them.

### Mechanism 3: ghOSt

A Google Research project that lets user-space BPF programs implement CPU scheduling policies. The kernel defers scheduling decisions to our BPF program for processes we've enrolled.

**Kernel requirement:** Linux 5.15+ with `CONFIG_SCHED_CLASS_EXT=y`. This is why Phase 3 builds a custom Alpine kernel with this flag enabled — Ubuntu's stock kernel does not have it.

**What it allows:** Processes enrolled in ghOSt have their CPU scheduling determined by our BPF policy (latency-sensitive, throughput-optimized, or background) rather than the kernel's default CFS scheduler.

---

## The Complete Picture

```
User: "I'm exporting video"
              ↓
Context Watcher detects ffmpeg process started
              ↓
Resource Governor (Python, user-space) receives event
Resource Governor calls: cgroups boost ffmpeg CPU weight to 600
Resource Governor calls: ghOSt enroll ffmpeg in THROUGHPUT policy
              ↓
Kernel applies changes immediately
              ↓
ffmpeg gets more CPU time, browser background tabs throttled
Export finishes faster — user didn't ask, OS predicted and acted
```

The AI never runs in the kernel. It observes the kernel through eBPF (a safe, kernel-provided interface) and steers the kernel through cgroups and ghOSt (standard kernel control interfaces).

---

## Phases for Kernel Integration

| Phase | Kernel interaction |
|-------|-------------------|
| 1–2 | None. Python processes run like any other user application. |
| 3 | Custom kernel compile flags enabled. Compositor uses DRM/KMS directly. |
| 4 | eBPF probes loaded. cgroups actuation. ghOSt scheduling policy. |

---

## Why This Matters for the Product

The "AI in the kernel" framing in the PRD is the correct intuition — but the implementation is user-space AI that speaks kernel fluently. This distinction matters because:

1. It is safe to deploy on real machines
2. It requires no kernel development expertise to build
3. eBPF is a production-grade technology used by Netflix, Cloudflare, Facebook at scale
4. The approach survives kernel version upgrades without recompilation
