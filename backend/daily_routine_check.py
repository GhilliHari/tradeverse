#!/usr/bin/env python3
"""
Tradeverse Angel One Daily Pre-Market Routine Check
Checks Angel One authentication, available cash/margins, positions, orders,
Oracle Cloud VM pulse, and risk controls.
"""

import os
import sys
import json
import logging
from datetime import datetime
import requests

# Set working directory to backend
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import config
from angel_client import AngelClient
from notifier import notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RoutineCheck")

def run_routine_check(send_telegram: bool = False) -> dict:
    now_ist = datetime.now()
    results = {
        "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
        "broker": config.ACTIVE_BROKER,
        "env": config.ENV,
        "trading_mode": config.TRADING_MODE,
        "angel_connected": False,
        "client_id": config.ANGEL_CLIENT_ID,
        "user_name": "N/A",
        "available_cash": 0.0,
        "open_positions_count": 0,
        "open_orders_count": 0,
        "cloud_vm_online": False,
        "cloud_pulse": {},
        "risk_limits": {
            "daily_loss_limit": config.DAILY_LOSS_LIMIT,
            "max_position_size": config.MAX_POSITION_SIZE,
            "max_open_positions": config.MAX_OPEN_POSITIONS,
            "min_confidence_gate": "68% (72% opening hour)",
            "cool_off_period": "10 min post-trade"
        },
        "errors": []
    }

    # 1. Test Angel One Connectivity & Session
    try:
        client = AngelClient(
            config.ANGEL_API_KEY,
            config.ANGEL_CLIENT_ID,
            config.ANGEL_PASSWORD,
            config.ANGEL_TOTP_KEY
        )
        if client.is_connected():
            results["angel_connected"] = True
            profile = client.profile()
            results["user_name"] = profile.get("user_name", "HARIDOSS LOGANATHAN")

            funds = client.get_funds()
            results["available_cash"] = float(funds.get("availablecash", 0.0))

            positions = client.positions() or []
            results["open_positions_count"] = len(positions)
            results["positions"] = positions

            orders = client.orders() or []
            pending_orders = [o for o in orders if str(o.get("status", "")).upper() in ("OPEN", "PENDING", "TRIGGER_PENDING")]
            results["open_orders_count"] = len(pending_orders)
        else:
            err = client.get_login_error() or "Unknown login error"
            results["errors"].append(f"Angel One Login Failed: {err}")
    except Exception as e:
        results["errors"].append(f"Angel Client Exception: {e}")

    # 2. Check Oracle Cloud VM Pulse
    cloud_ip = "129.225.125.13"
    ssh_key = os.path.expanduser("~/.ssh/oracle_tradeverse.key")
    try:
        # First try direct HTTP
        resp = requests.get(f"http://{cloud_ip}:8000/api/cloud/pulse", timeout=3)
        if resp.status_code == 200:
            results["cloud_vm_online"] = True
            results["cloud_pulse"] = resp.json()
    except Exception:
        # Fallback to SSH tunnel check as used in cloud_status.command
        if os.path.exists(ssh_key):
            try:
                import subprocess
                cmd = [
                    "ssh", "-i", ssh_key,
                    "-o", "ConnectTimeout=5",
                    "-o", "StrictHostKeyChecking=no",
                    f"opc@{cloud_ip}",
                    "curl -s http://127.0.0.1:8000/api/cloud/pulse"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                if proc.returncode == 0 and proc.stdout.strip():
                    pulse_data = json.loads(proc.stdout.strip())
                    results["cloud_vm_online"] = True
                    results["cloud_pulse"] = pulse_data
            except Exception as se:
                results["errors"].append(f"Cloud VM SSH check note: {se}")

    # 3. Format Telegram / Chat message
    status_icon = "✅" if results["angel_connected"] else "❌"
    cloud_icon = "🟢 Online" if results["cloud_vm_online"] else "🟡 Standby/Unreachable"
    
    msg_lines = [
        f"🛡️ *Tradeverse Angel One — Daily Routine Check*",
        f"⏱️ *Time:* `{results['timestamp']}`",
        f"🏦 *Broker:* `{results['broker']}` ({results['env']}) — {status_icon} *{'CONNECTED' if results['angel_connected'] else 'DISCONNECTED'}*",
        f"👤 *Client ID:* `{results['client_id']}` ({results['user_name']})",
        f"💰 *Available Cash:* *₹{results['available_cash']:,.2f}*",
        f"📊 *Open Positions:* `{results['open_positions_count']}`",
        f"📝 *Pending Orders:* `{results['open_orders_count']}`",
        f"☁️ *Oracle Cloud Engine:* {cloud_icon}",
        f"⚡ *Trading Mode:* `{results['trading_mode']}`",
        f"🔒 *Risk Caps:* Max ₹{results['risk_limits']['max_position_size']:,.0f} | Daily Loss Cap ₹{results['risk_limits']['daily_loss_limit']:,.0f}",
        f"🎯 *Safeguards:* Conf Gate $\ge$68% | 10m Cool-off | Tech Trend Veto Active"
    ]
    if results["errors"] and not results["angel_connected"]:
        msg_lines.append(f"⚠️ *Alerts:* {'; '.join(results['errors'])}")
        
    formatted_msg = "\n".join(msg_lines)
    results["formatted_message"] = formatted_msg

    # 4. Optional Telegram Notification
    if send_telegram and notifier.enabled:
        try:
            notifier.notify_sync(formatted_msg)
            results["telegram_sent"] = True
        except Exception as te:
            results["telegram_sent"] = False
            results["errors"].append(f"Telegram notification failed: {te}")

    # 5. Persist run log to disk for historical audit
    try:
        data_dir = os.path.join(BACKEND_DIR, "data")
        os.makedirs(data_dir, exist_ok=True)
        latest_file = os.path.join(data_dir, "latest_routine_check.json")
        history_file = os.path.join(data_dir, "routine_checks.jsonl")

        with open(latest_file, "w") as f:
            json.dump(results, f, indent=2)

        with open(history_file, "a") as f:
            f.write(json.dumps(results) + "\n")
    except Exception as fe:
        logger.warning(f"Could not save routine check log to disk: {fe}")

    return results

if __name__ == "__main__":
    send_tg = "--telegram" in sys.argv
    res = run_routine_check(send_telegram=send_tg)
    print(res["formatted_message"])
    if res.get("errors") and not res.get("angel_connected"):
        sys.exit(1)
    sys.exit(0)
