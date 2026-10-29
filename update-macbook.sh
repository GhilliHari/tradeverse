#!/bin/bash

# ==============================================================================
# 🔄 Tradeverse MacBook Exact-Clone Updater + Desktop App Installer
# ==============================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo "============================================================"
echo "🔄 Syncing MacBook with Exact iMac Tradeverse State..."
echo "============================================================"

# 1. Stop any old running backend/frontend/Electron processes
echo "🛑 Stopping old processes on ports 8000 & 5173..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# 2. Fetch & hard-reset to exact iMac state on GitHub
echo "📥 Pulling exact iMac files, models, settings & data from GitHub..."
git fetch origin main
git reset --hard origin/main

# 3. Ensure Backend Python .venv has all packages (including scipy, networkx, statsmodels)
cd "$SCRIPT_DIR/backend" || exit 1
if [ ! -x "./.venv/bin/python3" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi
echo "📦 Verifying Python dependencies (scipy, networkx, statsmodels, etc.)..."
./.venv/bin/pip install --upgrade pip -q
./.venv/bin/pip install -r requirements.txt -q

echo "📊 Syncing market-hours simulation & paper trades..."
./.venv/bin/python3 run_market_simulation.py --days 14 || true

# 4. Build & install Tradeverse AI.app onto MacBook Desktop & /Applications
cd "$SCRIPT_DIR" || exit 1
chmod +x ./build-macbook-app.sh
./build-macbook-app.sh
