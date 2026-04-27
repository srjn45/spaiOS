#!/usr/bin/env bash
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$SCRIPTS_DIR/stop.sh"
exec bash "$SCRIPTS_DIR/start.sh"
