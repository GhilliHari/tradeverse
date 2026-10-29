#!/bin/bash

# ==============================================================================
# 🔄 Tradeverse MacBook Exact-Clone Updater (100% Identical to iMac)
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

# 4. Ensure Frontend & Electron dependencies are installed and built
cd "$SCRIPT_DIR/frontend" || exit 1
if [ ! -d "./node_modules" ]; then
    echo "📦 Installing Frontend dependencies..."
    npm install
fi
npm run build

cd "$SCRIPT_DIR" || exit 1
if [ ! -d "./node_modules" ]; then
    echo "📦 Installing Electron Desktop dependencies..."
    npm install
fi

# 5. If Tradeverse AI.app is in /Applications, update it to match iMac
if [ -d "/Applications/Tradeverse AI.app" ]; then
    echo "🖥️ Updating /Applications/Tradeverse AI.app..."
    npm run pack || true
    if [ -d "./dist_desktop/mac-arm64/Tradeverse AI.app" ]; then
        rm -rf "/Applications/Tradeverse AI.app"
        cp -R "./dist_desktop/mac-arm64/Tradeverse AI.app" "/Applications/"
        echo "✅ /Applications/Tradeverse AI.app updated!"
    fi
fi

echo ""
echo "✅ MacBook is now 100% identical to your iMac!"
echo "🚀 Launching Tradeverse Desktop Suite (Backend + Frontend + Electron)..."
npm run desktop
