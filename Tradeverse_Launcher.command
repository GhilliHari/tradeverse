#!/bin/bash

# ==============================================================================
# 🚀 Tradeverse MacBook & Investor Demo 1-Click Launcher
# ==============================================================================
# Works out-of-the-box on any MacBook / Mac:
#   1. Syncs latest backup data & simulation logs from GitHub
#   2. Auto-creates Python .venv & installs dependencies if missing
#   3. Auto-builds ML models from GitHub-backed cache if missing
#   4. Runs market-hours simulation catch-up
#   5. Auto-installs Frontend node_modules if missing
#   6. Starts Backend (8000) + Frontend (5173) and opens the Investor Demo UI
# ==============================================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
URL="http://localhost:5173"

cd "$SCRIPT_DIR" || exit 1

echo "=================================================="
echo "🚀 Launching Tradeverse Investor Demo System"
echo "📂 Directory: $SCRIPT_DIR"
echo "=================================================="

# 1. Pull latest backup data from GitHub if online
echo "🔄 Checking GitHub for latest backup data..."
GIT_TERMINAL_PROMPT=0 git pull origin main --no-edit 2>/dev/null || echo "ℹ️ Running with local GitHub backup cache."

# 2. Ensure Backend Python Virtual Environment & all packages (scipy, sklearn, etc.) are ready
cd "$BACKEND_DIR" || exit 1
if [ ! -x "./.venv/bin/python3" ]; then
    echo "📦 Setting up Python virtual environment on this MacBook..."
    python3 -m venv .venv
    ./.venv/bin/pip install --upgrade pip
    ./.venv/bin/pip install -r requirements.txt
elif ! ./.venv/bin/python3 -c "import scipy, networkx, sklearn, fastapi, pandas, yfinance" >/dev/null 2>&1; then
    echo "📦 Installing missing Python packages (scipy, networkx, etc.)..."
    ./.venv/bin/pip install -r requirements.txt
fi

# 3. Ensure ML model artifacts exist (built from GitHub-backed cache)
if [ ! -f "./market_model_daily.joblib" ] || [ ! -f "./market_model_intraday.joblib" ]; then
    echo "🧠 Building local AI model artifacts from GitHub backup cache..."
    ./.venv/bin/python3 train_lite.py || true
fi

# 4. Sync market-hours simulation trades before demo starts
echo "📊 Syncing market-hours simulation & paper trading ledger..."
./.venv/bin/python3 run_market_simulation.py --days 14 || true

# 5. Ensure Frontend dependencies are installed
cd "$FRONTEND_DIR" || exit 1
if [ ! -d "./node_modules" ]; then
    echo "📦 Installing Frontend dependencies on this MacBook..."
    npm install
fi

# 6. Clean up any old processes on ports 8000 and 5173
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# 7. Launch Backend Server (with caffeinate so MacBook doesn't sleep during demo)
echo "⚡ Starting Tradeverse AI Backend (Port 8000)..."
osascript -e "
tell application \"Terminal\"
    do script \"cd '$BACKEND_DIR' && echo '⚡ Tradeverse AI Backend Running...' && /usr/bin/caffeinate -dims ./.venv/bin/python3 main.py\"
end tell" 2>/dev/null || (cd "$BACKEND_DIR" && nohup /usr/bin/caffeinate -dims ./.venv/bin/python3 main.py > backend_demo.log 2>&1 &)

# 8. Launch Frontend Server (Port 5173)
echo "💻 Starting Tradeverse Frontend UI (Port 5173)..."
osascript -e "
tell application \"Terminal\"
    do script \"cd '$FRONTEND_DIR' && echo '💻 Tradeverse UI Running...' && npm run dev -- --host\"
end tell" 2>/dev/null || (cd "$FRONTEND_DIR" && nohup npm run dev -- --host > frontend_demo.log 2>&1 &)

# 9. Wait for Frontend port 5173 to be ready, then open browser
echo "⏳ Waiting for Tradeverse UI to come online..."
for i in {1..20}; do
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "🌐 Opening Tradeverse Investor Demo at $URL..."
open "$URL"

echo "✅ Tradeverse Investor Demo is LIVE!"
