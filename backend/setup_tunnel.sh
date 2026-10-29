#!/bin/bash
# ============================================================
# Tradeverse - Cloudflare Tunnel One-Time Setup
# Installs cloudflared without requiring Homebrew.
# Run this ONCE from the backend directory.
# ============================================================

set -e

echo ""
echo "🌩️  Tradeverse Cloudflare Tunnel Setup"
echo "======================================="
echo ""

# 1. Check if cloudflared is already installed
if command -v cloudflared &> /dev/null; then
    echo "✅ cloudflared is already installed: $(cloudflared --version)"
    echo ""
    echo "🎉 Nothing to do! Run the tunnel with:"
    echo "  python3 start_tunnel.py"
    exit 0
fi

# 2. Detect Mac architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    BINARY_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64"
    echo "🔍 Detected: Apple Silicon (arm64)"
else
    BINARY_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
    echo "🔍 Detected: Intel Mac (amd64)"
fi

# 3. Download binary
INSTALL_PATH="/usr/local/bin/cloudflared"
echo "📦 Downloading cloudflared binary..."
curl -fsSL --location --output /tmp/cloudflared_download "$BINARY_URL"
chmod +x /tmp/cloudflared_download

# 4. Move to /usr/local/bin (requires sudo)
echo "🔐 Installing to $INSTALL_PATH (may ask for your password)..."
sudo mv /tmp/cloudflared_download "$INSTALL_PATH"

echo ""
echo "✅ cloudflared installed: $(cloudflared --version)"
echo ""
echo "🎉 Setup Complete! Start the tunnel with:"
echo "  python3 start_tunnel.py"
echo ""
echo "The URL will be printed. Update VITE_API_URL in Vercel with it."
echo ""
