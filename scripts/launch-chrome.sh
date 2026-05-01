#!/usr/bin/env bash
# Launch Google Chrome with the CDP debug port open on 9222.
# spaiOS ChromeAgent connects to this port to control the browser.
# If Chrome is already running with --remote-debugging-port=9222, this is a no-op.

set -e

PORT=9222

if curl -s "http://localhost:${PORT}/json/version" &>/dev/null; then
    echo "Chrome is already running with debug port ${PORT}."
    exit 0
fi

CHROME_BIN=$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)

if [ -z "$CHROME_BIN" ]; then
    echo "Error: no Chrome/Chromium binary found on PATH." >&2
    exit 1
fi

DATA_DIR="${HOME}/.config/chrome-spaiOS"

echo "Launching Chrome with remote debugging on port ${PORT}..."
"$CHROME_BIN" \
    --remote-debugging-port="${PORT}" \
    --user-data-dir="${DATA_DIR}" \
    --no-first-run \
    --no-default-browser-check \
    &

echo "Chrome started (PID $!)."
