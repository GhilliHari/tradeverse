#!/bin/bash

# ==============================================================================
# 🖥️ Tradeverse AI — Native MacBook Desktop App Builder & Installer
# ==============================================================================
# Builds "Tradeverse AI.app" and installs it directly onto:
#   1. Your MacBook Desktop (~/Desktop/Tradeverse AI.app)
#   2. Your Applications Folder (/Applications/Tradeverse AI.app)
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🖥️ Building Native MacBook App: Tradeverse AI.app"
echo "============================================================"

# 1. Record local backend path so Tradeverse AI.app can auto-start Python backend
cat > "$SCRIPT_DIR/backend-path.json" <<EOF
{
  "backendDir": "$SCRIPT_DIR/backend"
}
EOF

# 2. Ensure Frontend is built
echo "📦 Building latest Frontend UI bundle..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "./node_modules" ]; then
    npm install
fi
npm run build

# 3. Ensure root Electron builder dependencies exist
cd "$SCRIPT_DIR"
if [ ! -d "./node_modules" ]; then
    npm install
fi

# 4. Package Tradeverse AI.app
echo "🔨 Packaging macOS Native Application (Tradeverse AI.app)..."
npx electron-builder --dir

# 5. Locate built .app bundle (mac-arm64 or mac)
APP_BUNDLE=""
if [ -d "$SCRIPT_DIR/dist_desktop/mac-arm64/Tradeverse AI.app" ]; then
    APP_BUNDLE="$SCRIPT_DIR/dist_desktop/mac-arm64/Tradeverse AI.app"
elif [ -d "$SCRIPT_DIR/dist_desktop/mac/Tradeverse AI.app" ]; then
    APP_BUNDLE="$SCRIPT_DIR/dist_desktop/mac/Tradeverse AI.app"
fi

if [ -z "$APP_BUNDLE" ]; then
    echo "❌ Could not find built Tradeverse AI.app in dist_desktop/"
    exit 1
fi

# 6. Copy to MacBook Desktop and /Applications
echo "📲 Installing 'Tradeverse AI.app' to Desktop and /Applications..."
rm -rf "$HOME/Desktop/Tradeverse AI.app"
cp -R "$APP_BUNDLE" "$HOME/Desktop/Tradeverse AI.app"

rm -rf "/Applications/Tradeverse AI.app" 2>/dev/null || true
cp -R "$APP_BUNDLE" "/Applications/Tradeverse AI.app" 2>/dev/null || true

echo ""
echo "✅ SUCCESS! 'Tradeverse AI' is now on your MacBook Desktop & Applications!"
echo "   • Desktop Icon: ~/Desktop/Tradeverse AI.app"
echo "   • Applications: /Applications/Tradeverse AI.app"
echo ""
echo "🚀 Opening Tradeverse AI Desktop App..."
open "$HOME/Desktop/Tradeverse AI.app"

