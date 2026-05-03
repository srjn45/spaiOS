# Task: P3-M4 — LiteLLM Multi-Model Routing

**Date:** 2026-05-03
**Phase:** Phase 3 — The Assistant Layer
**Session goal:** Replace spaid's single-provider router with LiteLLM. Priority queue with auto-fallback.
**Notion task ID:** phase3_m4_litellm_routing
**Repo:** spaiSH

## What We're Building

spaid currently routes to one configured endpoint. Replace the router with LiteLLM so users can configure a priority list of models (Claude → GPT-4o-mini → local Ollama) with automatic fallback on rate limits, errors, or network loss.

## Approach

1. Add LiteLLM as a Go dependency or run it as a sidecar proxy:
   - **Option A (recommended):** LiteLLM as a local proxy (`litellm --config ~/.config/spaish/litellm.yaml --port 4000`). spaid talks to `http://localhost:4000` as if it were an OpenAI endpoint. Simplest integration — no Go changes to the LLM client.
   - **Option B:** Use LiteLLM Python SDK directly, called via spaid subprocess. More coupling.
   - Choose Option A: sidecar proxy started by the installer, managed as a systemd user service alongside spaid.
2. Add `~/.config/spaish/litellm.yaml` config:
   ```yaml
   model_list:
     - model_name: primary
       litellm_params:
         model: claude-3-5-haiku-20241022
         api_key: os.environ/ANTHROPIC_API_KEY
     - model_name: primary
       litellm_params:
         model: gpt-4o-mini
         api_key: os.environ/OPENAI_API_KEY
     - model_name: primary
       litellm_params:
         model: ollama/qwen2.5-coder
         api_base: http://localhost:11434
   router_settings:
     routing_strategy: least-busy
     fallbacks: [{"primary": ["primary"]}]
   ```
3. Update `~/.config/spaish/spaid.toml` to point at litellm proxy:
   ```toml
   [provider]
   endpoint = "http://localhost:4000"
   model = "primary"
   ```
4. Update installer to: `pip install litellm`, write `litellm.service` systemd unit, start it
5. Test priority and fallback behaviour

## Files Touched (spaiSH)

- `config/spaid.toml` — update default to point at litellm
- `config/litellm.yaml` — new default config template
- `cmd/spaid/main.go` — minor: use `primary` as model name

## Files Touched (spaiOS installer)

- `scripts/spai-install.sh` — add litellm install + service

## Done When

- [ ] With `ANTHROPIC_API_KEY` set, queries route to Claude haiku
- [ ] With only `OPENAI_API_KEY`, queries route to GPT-4o-mini
- [ ] With no API keys + Ollama running, queries go to local qwen2.5-coder
- [ ] Kill network mid-session → falls back to Ollama transparently
- [ ] `spai ask me anything` confirms which model answered (log shows provider)
