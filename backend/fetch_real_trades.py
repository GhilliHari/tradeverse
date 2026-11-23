#!/usr/bin/env python3
"""
Fetch Live Real-Money Trade Status from Angel One Broker
"""
import sys
import os
import json

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config import config
from angel_client import AngelClient

def main():
    print(f"Connecting to Angel One (Client ID: {config.ANGEL_CLIENT_ID})...")
    client = AngelClient(
        config.ANGEL_API_KEY,
        config.ANGEL_CLIENT_ID,
        config.ANGEL_PASSWORD,
        config.ANGEL_TOTP_KEY
    )
    
    if not client.is_connected():
        print(f"❌ Connection Failed: {client.get_login_error()}")
        sys.exit(1)
        
    print("✅ Successfully authenticated with Angel One!")
    profile = client.profile()
    funds = client.get_funds()
    orders = client.orders()
    positions = client.positions()
    
    trades = []
    if client.smart_api:
        try:
            tb_res = client.smart_api.tradeBook()
            if tb_res and tb_res.get("status"):
                trades = tb_res.get("data") or []
        except Exception as e:
            print(f"TradeBook fetch note: {e}")

    result = {
        "client_id": config.ANGEL_CLIENT_ID,
        "user_name": profile.get("user_name", "N/A"),
        "funds": funds,
        "total_orders_today": len(orders),
        "orders": orders,
        "total_positions_today": len(positions),
        "positions": positions,
        "total_executed_trades_today": len(trades),
        "trades": trades
    }
    
    print("\n--- REAL MONEY STATUS DUMP ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
