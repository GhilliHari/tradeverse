#!/bin/bash

# ==============================================================================
# 🔄 Tradeverse MacBook 1-Step Updater (Updates Code, Backup Data & Desktop App)
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🔄 Updating Tradeverse on this MacBook to Latest Version..."
echo "============================================================"

# 1. Fetch & reset to latest main branch from GitHub
git fetch origin main
git reset --hard origin/main

# 2. Update Backend Python dependencies & sync simulation backup data
cd "$SCRIPT_DIR/backend"
if [ ! -x "./.venv/bin/python3" ]; then
    python3 -m venv .venv
fi
./.venv/bin/pip install --upgrade pip -q
./.venv/bin/pip install -r requirements.txt -q

if [ ! -f "./market_model_daily.joblib" ] || [ ! -f "./market_model_intraday.joblib" ]; then
    echo "🧠 Rebuilding local ML models from GitHub-backed cache..."
    ./.venv/bin/python3 train_lite.py || true
fi

echo "📊 Syncing latest market-hours simulation & paper trades..."
./.venv/bin/python3 run_market_simulation.py --days 14 || true

# 3. Update Frontend dependencies & build production bundle
cd "$SCRIPT_DIR/frontend"
npm install
npm run build

# 4. Rebuild macOS Native Desktop App (Tradeverse AI.app) if electron-builder is installed
cd "$SCRIPT_DIR"
if [ -d "./node_modules" ]; then
    echo "🖥️ Updating macOS Desktop App (Tradeverse AI.app)..."
    npm run pack || true
    if [ -d "./dist_desktop/mac-arm64/Tradeverse AI.app" ] && [ -d "/Applications/Tradeverse AI.app" ]; then
        rm -rf "/Applications/Tradeverse AI.app"
        cp -R "./dist_desktop/mac-arm64/Tradeverse AI.app" "/Applications/"
        echo "✅ Updated /Applications/Tradeverse AI.app!"
    fi
fi

echo ""
echo "✅ MacBook is now running the LATEST Tradeverse version!"
echo "🚀 Launching Tradeverse Now..."
./Tradeverse_Launcher.command
