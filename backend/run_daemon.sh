#!/bin/bash
# Headless 24/7 Background Service Runner for Tradeverse Backend
# Prevents macOS idle sleep during market hours and auto-backfills any missed market hours on boot/wake.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
cd "$BACKEND_DIR" || exit 1

PYTHON_BIN="python3"
if [ -x "$BACKEND_DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python3"
fi

# Run immediate offline market-hours catch-up before launching server
"$PYTHON_BIN" "$BACKEND_DIR/run_market_simulation.py" --days 14 || true

if [ -x "/usr/bin/caffeinate" ]; then
    exec /usr/bin/caffeinate -dims "$PYTHON_BIN" main.py
else
    exec "$PYTHON_BIN" main.py
fi
