"""
Tradeverse - Cloudflare Tunnel Launcher
---------------------------------------
Uses `cloudflared tunnel --url` (trycloudflare.com) which is:
  - FREE — no account or login needed
  - Produces a stable URL tied to this config file's tunnel ID
  - No warning/interstitial pages (unlike ngrok/pinggy free tiers)
  - Works from Indian residential IPs (bypasses Angel One geo-block)

Usage:
    python3 start_tunnel.py

The tunnel URL will be printed. Copy it into:
  - Vercel → Environment Variables → VITE_API_URL
"""

import subprocess
import re
import sys
import time
import signal


import os as _os
import pathlib as _pathlib

BACKEND_PORT = 8000

# Prefer the local binary (downloaded by setup_tunnel.sh) over system PATH
_local_bin = _pathlib.Path(__file__).parent / "cloudflared"
CLOUDFLARED_BIN = str(_local_bin) if _local_bin.exists() else "cloudflared"

CLOUDFLARED_CMD = [
    CLOUDFLARED_BIN, "tunnel",
    "--url", f"http://localhost:{BACKEND_PORT}",
    "--no-autoupdate"
]


def main():
    print()
    print("=" * 60)
    print("  🌩️  Tradeverse — Cloudflare Tunnel")
    print("=" * 60)
    print(f"  Tunneling http://localhost:{BACKEND_PORT} → internet")
    print("  Waiting for tunnel URL (this takes ~5 seconds)...")
    print()

    tunnel_url = None

    try:
        process = subprocess.Popen(
            CLOUDFLARED_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Register signal handlers for clean shutdown
        def shutdown(sig, frame):
            print("\n\n🛑 Shutting down Cloudflare tunnel...")
            process.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        # Parse the URL from cloudflared output
        url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")

        for line in process.stdout:
            sys.stdout.flush()
            match = url_pattern.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                print("=" * 60)
                print("  ✅ TUNNEL IS LIVE!")
                print()
                print(f"  TUNNEL URL:  {tunnel_url}")
                print()
                print("  → Copy this URL into Vercel:")
                print("    Dashboard → Settings → Environment Variables")
                print(f"    VITE_API_URL = {tunnel_url}")
                print()
                print("  Press Ctrl+C to stop the tunnel.")
                print("=" * 60)
                print()

        # Wait for process to finish (keeps tunnel alive)
        process.wait()

    except FileNotFoundError:
        print("❌ ERROR: 'cloudflared' not found.")
        print()
        print("   Run the setup script first:")
        print("     bash setup_tunnel.sh")
        print()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
