#!/bin/bash

# Configuration
BACKEND_DIR="/Users/teju/.gemini/antigravity/scratch/tradeverse/backend"
FRONTEND_DIR="/Users/teju/.gemini/antigravity/scratch/tradeverse/frontend"
URL="http://localhost:5173"

echo "🚀 Launching Tradeverse System..."

# Launch Backend in a new Terminal window
echo "Starting Backend Server..."
osascript -e "
tell application \"Terminal\"
    do script \"cd '$BACKEND_DIR' && echo 'Starting Tradeverse Backend...' && python3 main.py\"
end tell"

# Launch Frontend in a new Terminal window
echo "Starting Frontend Server..."
osascript -e "
tell application \"Terminal\"
    do script \"cd '$FRONTEND_DIR' && echo 'Starting Tradeverse Frontend...' && npm run dev\"
end tell"

# Wait for servers to initialize
echo "Waiting for systems to come online..."
sleep 5

# Open Dashboard in default browser
echo "Opening Dashboard..."
open "$URL"

echo "✅ Tradeverse Launched Successfully!"
