#!/usr/bin/env bash
set -euo pipefail

pkill -f ".venv/bin/spaiOS" 2>/dev/null || true
pkill -f "uv run spaiOS" 2>/dev/null || true

sleep 0.5
