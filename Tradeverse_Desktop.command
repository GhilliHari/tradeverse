#!/bin/bash

# ==============================================================================
# 🖥️ Tradeverse Native MacBook Desktop App Launcher (Electron)
# ==============================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || { echo "❌ Directory not found at $SCRIPT_DIR"; exit 1; }

echo "🚀 Starting Tradeverse Native MacBook Desktop App..."

if ! command -v npm &> /dev/null; then
    echo "❌ npm could not be found. Please ensure Node.js is installed on your MacBook."
    exit 1
fi

# 1. Pull latest GitHub backup data
GIT_TERMINAL_PROMPT=0 git pull origin main --no-edit 2>/dev/null || true

# 2. Ensure Backend .venv exists
if [ ! -x "$SCRIPT_DIR/backend/.venv/bin/python3" ]; then
    echo "📦 Creating Backend Python environment..."
    cd "$SCRIPT_DIR/backend" && python3 -m venv .venv && ./.venv/bin/pip install --upgrade pip && ./.venv/bin/pip install -r requirements.txt
    cd "$SCRIPT_DIR"
fi

# 3. Ensure ML models & simulation data are synced
cd "$SCRIPT_DIR/backend"
if [ ! -f "./market_model_daily.joblib" ] || [ ! -f "./market_model_intraday.joblib" ]; then
    ./.venv/bin/python3 train_lite.py || true
fi
./.venv/bin/python3 run_market_simulation.py --days 14 || true
cd "$SCRIPT_DIR"

# 4. Ensure root & frontend node_modules exist
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "📦 Installing Desktop Electron dependencies..."
    npm install
fi
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "📦 Installing Frontend UI dependencies..."
    cd "$SCRIPT_DIR/frontend" && npm install && cd "$SCRIPT_DIR"
fi

# 5. Launch Electron Desktop Suite
npm run desktop
