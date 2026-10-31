import subprocess
import re
import sys
import time
import signal
import os
import threading
import qrcode
import atexit

# Configuration
FRONTEND_PORT = 5173
BACKEND_PORT = 8000
# Dynamically resolve project directory based on this script's location
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_BIN = os.path.join(PROJECT_DIR, "backend/cloudflared")

# Use local binary if exists, else system cloudflared
CLOUDFLARED_BIN = BACKEND_BIN if os.path.exists(BACKEND_BIN) else "cloudflared"

# Global subprocesses list for clean exit
processes = []
env_file_path = os.path.join(PROJECT_DIR, "frontend/.env")
original_env_content = None

def restore_env():
    """Restore the original .env content on exit."""
    if original_env_content is not None:
        print("\n🔄 Restoring original frontend/.env configuration...")
        try:
            with open(env_file_path, "w") as f:
                f.write(original_env_content)
            print("✅ frontend/.env restored.")
        except Exception as e:
            print(f"⚠️ Failed to restore frontend/.env: {e}")

def update_env(backend_url):
    """Update VITE_API_URL in frontend/.env, backing up original first."""
    global original_env_content
    print(f"\n⚙️ Updating frontend/.env with VITE_API_URL = {backend_url}")
    
    if os.path.exists(env_file_path):
        try:
            with open(env_file_path, "r") as f:
                original_env_content = f.read()
        except Exception as e:
            print(f"⚠️ Failed to read frontend/.env: {e}")
            original_env_content = ""
    else:
        original_env_content = ""

    # Parse and update VITE_API_URL
    lines = original_env_content.splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("VITE_API_URL="):
            new_lines.append(f"VITE_API_URL={backend_url}")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        new_lines.append(f"VITE_API_URL={backend_url}")
        
    try:
        with open(env_file_path, "w") as f:
            f.write("\n".join(new_lines) + "\n")
        print("✅ frontend/.env updated successfully.")
    except Exception as e:
        print(f"❌ Failed to write to frontend/.env: {e}")
        sys.exit(1)

def print_qr(url):
    qr = qrcode.QRCode(version=1, box_size=1, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

def start_tunnel(port, name):
    """Start a cloudflared tunnel for the given port and return the process and tunnel URL."""
    cmd = [
        CLOUDFLARED_BIN, "tunnel",
        "--url", f"http://localhost:{port}",
        "--no-autoupdate"
    ]
    print(f"🌩️ Starting tunnel for {name} (port {port})...")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(process)
        
        url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
        tunnel_url = None
        
        # Read stdout to grab the trycloudflare URL
        start_time = time.time()
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                break
            
            # Timeout after 15 seconds
            if time.time() - start_time > 15:
                print(f"❌ Timeout waiting for {name} tunnel URL.")
                process.terminate()
                sys.exit(1)
                
        if not tunnel_url:
            print(f"❌ Failed to obtain tunnel URL for {name}.")
            process.terminate()
            sys.exit(1)

        # Drain stdout continuously in background thread so OS pipe buffer never fills and deadlocks cloudflared
        def _drain_stdout(proc):
            try:
                for _ in proc.stdout:
                    pass
            except Exception:
                pass

        threading.Thread(target=_drain_stdout, args=(process,), daemon=True).start()
            
        print(f"✅ {name} tunnel live at: {tunnel_url}")
        return process, tunnel_url
        
    except Exception as e:
        print(f"❌ Error starting tunnel for {name}: {e}")
        sys.exit(1)

def check_port(port):
    """Check if a local port is open/active."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

def main():
    print("\n" + "="*60)
    print("📱 Tradeverse Mobile Access Bridge")
    print("="*60)
    
    # 1. Register cleanup
    atexit.register(restore_env)
    
    # 2. Check if servers are running
    backend_running = check_port(BACKEND_PORT)
    frontend_running = check_port(FRONTEND_PORT)
    
    if not backend_running:
        print("⚠️ Backend server is not running on port 8000!")
        print("💡 Please make sure to run the backend server first (e.g. using Tradeverse_Launcher.command)")
        sys.exit(1)
        
    if not frontend_running:
        print("⚠️ Frontend server is not running on port 5173!")
        print("💡 Please make sure to run the frontend server first (e.g. using Tradeverse_Launcher.command)")
        sys.exit(1)

    # 3. Start Backend Tunnel
    backend_process, backend_url = start_tunnel(BACKEND_PORT, "Backend")
    
    # 4. Keep frontend/.env clean (Vite proxy on port 5173 routes /api and /backend-status directly to localhost:8000)
    print(f"\n⚙️ Routing API via Vite proxy (/api -> http://localhost:{BACKEND_PORT}) so both localhost and remote tunnel work simultaneously.")
    
    # 5. Start Frontend Tunnel
    frontend_process, frontend_url = start_tunnel(FRONTEND_PORT, "Frontend")
    
    print("\n" + "="*60)
    print("✅ YOUR MOBILE ACCESS IS LIVE!")
    print(f"👉 Frontend (App): {frontend_url}")
    print(f"👉 Backend (API):  {backend_url}")
    print("-" * 60)
    print("Scan this QR code with your phone camera to open the App:")
    print_qr(frontend_url)
    print("\nOpen this link on your phone (Chrome/Safari) to access Tradeverse.")
    print("-" * 60)
    print("Keep this terminal open while you use the app on mobile.")
    print("Press Ctrl+C to stop the tunnel and exit.")
    print("="*60 + "\n")
    
    # Register signal handlers for clean exit
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down tunnels...")
        for p in processes:
            p.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait on both processes
    while True:
        # Check if any process died
        if backend_process.poll() is not None:
            print("⚠️ Backend tunnel disconnected.")
            break
        if frontend_process.poll() is not None:
            print("⚠️ Frontend tunnel disconnected.")
            break
        time.sleep(1)
        
    # Trigger exit/restore via sys.exit
    sys.exit(0)

if __name__ == "__main__":
    main()
