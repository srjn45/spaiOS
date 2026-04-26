# Product Requirements Document: spaiOS
**"The OS that understands the vibe."**

## 1. Executive Summary
**spaiOS** (Srajan Pathak AI OS) is a visionary, AI-native operating system designed to transition computing from an "Application + File" paradigm to an "Intent + Agent" model. Built for the modern "vibe coding" era, spaiOS acts as a proactive partner—a "Jarvis-like" intelligence—that natively understands natural language, generates UI on the fly, and manages hardware resources at the kernel level using AI. 

**Target Audience:** Non-technical users, casual creatives, and "vibe coders" who want high-level execution without managing files, syntax, or applications.

## 2. Core Philosophy & Pillars
1. **Intent over Syntax:** Users describe what they want to achieve; the OS handles the *how*.
2. **Proactive Assistance:** The OS anticipates needs via localized, lightweight background "Watchers."
3. **Generative UI:** No static desktop or traditional window management. Interfaces are built dynamically based on the active intent and agent requirements.
4. **Local-First & Private:** Default processing happens entirely on-device using local models. Cloud connections are strictly opt-in via API configurations.

---

## 3. Final OS Architecture & Requirements

### 3.1 Base Architecture
* **Kernel:** Forked lightweight Linux distribution (e.g., Alpine or Arch) optimized for minimal overhead.
* **Scheduling:** "Neural Scheduler" running in User-Space (via technologies like `ghOSt`), prioritizing CPU/NPU/GPU allocation based on AI-predicted user tasks, rather than standard round-robin scheduling.
* **Hardware Support:** Scalable from basic laptops with integrated GPUs to high-performance machines, and eventually ARM devices (Raspberry Pi, smartphones).

### 3.2 AI Intelligence Swarm
spaiOS uses a Multi-Agent Swarm architecture:
* **The Orchestrator:** The primary decision-maker (powered by local Llama 3 or Gemma). Routes intent to specialized agents.
* **The Watchers:** Ultra-lightweight models (e.g., BitNet 1.58b) running constantly in the background with minimal power draw.
  * *Vision Watcher:* Monitors on-screen context locally.
  * *Context Watcher:* Maintains short-term memory of recent tasks.
  * *Resource Watcher:* Pre-emptively manages RAM and thermal load.
* **Specialized Task Agents:** Media Agent, File Agent, Code Agent, etc.

### 3.3 Interoperability 
* **Universal AI Interface:** Utilization of the **Model Context Protocol (MCP)**. This acts as the standard "AI bus," allowing users to plug in cloud-based API keys (GPT-4, Claude) seamlessly alongside local models.

### 3.4 Visual Identity & UI
* **Display Engine:** Custom Wayland Compositor written in Rust.
* **The Common Interface:** The **"Neural Sphere"**—a pulsating, geometric, network-of-nodes visualization that acts as the focal point of AI interaction.
  * *Idle:* Slow heartbeat pulse.
  * *Thinking:* Random nodes sparking and connecting.
  * *Action:* Sphere morphs into Generative UI windows based on `[UI_BLUEPRINT]` JSON outputs.
* **The "Vibe" Toggle (Performance Settings):**
  * **Quiet Mode:** Reactive only. Watchers off. Minimal resource usage.
  * **Partner Mode:** Balanced. Periodic Watcher activity. Moderate resource usage.
  * **Jarvis Mode:** Always-on context awareness and full generative capabilities. High resource usage.

---

## 4. Phase 1 Prototype: The Sandbox

Before altering the kernel, a functional prototype will be built to validate the "vibe" and agent interaction. This Sandbox will run on existing operating systems (Windows/macOS/Linux).

### 4.1 Sandbox Tech Stack
* **Language/Framework:** Python-based "OS Wrapper".
* **Local Inference:** Ollama running Llama 3 (8B) or similar model.
* **Agent Framework:** LangChain or CrewAI for routing and tool execution.
* **Memory:** Local Vector Database (ChromaDB) to retain user identity (e.g., Srajan) and preferences.
* **UI/Visuals:** PyQt6, CustomTkinter, or Manim to render the floating "Neural Sphere" overlay.

### 4.2 Initial Boot Experience (The "First Breath")
* **Interaction:** Black screen with a slowly fading-in Neural Sphere. The AI introduces itself via text/voice, calibrates to the hardware, and asks for the user's name.
* **Action:** Upon learning the user's name, it scans a designated sandboxed folder and provides a proactive suggestion (e.g., "I see some cluttered files, shall I organize them?").

### 4.3 MVP "First Five" Capabilities
The Sandbox must successfully execute the following commands in a contained environment:
1. **"spaiOS, organize my clutter."** (File Agent sorts a messy sandbox folder).
2. **"I need to focus on my photos."** (Generative UI clears screen and renders a minimal photo gallery).
3. **"Summarize what I've been doing."** (Context Watcher reads mock history logs and provides a summary).
4. **"Make this photo look like a 90s film."** (Media Agent executes a local python image processing script).
5. **"Set up a workspace for Tokyo."** (Orchestrator creates a mock virtual desktop with related browser tabs and notes).

---

## 5. Development Roadmap
* **Milestone 1: The Python Nexus (Sandbox)**
  * Establish Ollama connection, ChromaDB memory, and the core Orchestrator System Prompt.
  * Build the floating Neural Sphere UI.
  * Implement the File Agent in a sandbox directory.
* **Milestone 2: The Generative UI Engine**
  * Transition from standard Python UI to a custom renderer capable of translating AI JSON blueprints into functional UI cards.
  * Integrate the MCP for switching to cloud-based APIs.
* **Milestone 3: The Custom Linux Fork**
  * Strip down Alpine/Arch Linux.
  * Implement the Wayland Compositor.
  * Move Watcher agents to background system processes (systemd).
* **Milestone 4: The Neural Scheduler**
  * Connect spaiOS resource management to the Linux kernel via ghOSt.
  * Optimize for edge hardware and Raspberry Pi deployments.

---
*Document Version: 1.0 | Date: April 2026*
