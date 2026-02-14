import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def wait_for_server():
    print("Waiting for server...")
    for _ in range(30):
        try:
            r = requests.get(f"{BASE_URL}/api/health")
            if r.status_code == 200:
                print("Server is UP!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def run_test():
    if not wait_for_server():
        print("Server failed to start.")
        sys.exit(1)

    print("\n1. Placing Paper Trade...")
    trade_payload = {
        "symbol": "NSE:BANKNIFTY",
        "side": "BUY",
        "quantity": 15,
        "price": 45000.0,
        "reasoning": "Integration Test Buy",
        "mode": "TEST"
    }
    # Mock Auth Token (Assuming dev mode allows any token or we disable auth for test)
    # The current auth_middleware.py likely requires a Firebase token.
    # We might need to mock get_current_user in main.py or use a valid token.
    # For now, let's assume we can get by or the backend is in a mode that accepts a dummy if verified.
    # Actually, main.py uses `Depends(get_current_user)`.
    # I'll need to bypass auth or use a test token.
    # Strategy: I'll temporarily disable auth in main.py OR I'll mock the auth middleware.
    # Easier: I'll mock the auth middleware in this test file? No, I can't inject into running server. 
    # I will modify the headers to simulate a test user if possible, or just expect 403 and fix it.
    
    # Wait, `get_current_user` usually verifies a Firebase token.
    # If I can't generate one, I should disable auth for `/api/paper` temporarily or use a MOCK_USER env var.
    
    # Let's try sending a dummy token and see if `auth_middleware` accepts it in MOCK/DEV mode.
    # Reviewing `auth_middleware.py`... (I don't have it visible, but usually it checks Firebase).
    # If it fails, I will use `replace_file_content` to bypass auth for the test.
    
    headers = {"Authorization": "Bearer TEST_TOKEN"}
    
    try:
        r = requests.post(f"{BASE_URL}/api/paper/trade", json=trade_payload, headers=headers)
        if r.status_code == 401 or r.status_code == 403:
            print("Auth failed. Please disable auth for verification.")
            return

        print(f"Trade Response: {r.status_code} {r.json()}")
        trade_id = r.json()['trade']['trade_id']
        
        print(f"\n2. Closing Paper Trade {trade_id}...")
        close_payload = {
            "trade_id": trade_id,
            "exit_price": 45100.0,
            "reasoning": "Integration Test Close"
        }
        r = requests.post(f"{BASE_URL}/api/paper/close", json=close_payload, headers=headers)
        print(f"Close Response: {r.status_code} {r.json()}")

        print("\n3. Verifying History...")
        r = requests.get(f"{BASE_URL}/api/paper/history", headers=headers)
        history = r.json()
        print(f"History Length: {len(history)}")
        
        found = any(h['trade_id'] == trade_id for h in history)
        if found:
            print("✅ TEST PASSED: Trade found in history.")
        else:
            print("❌ TEST FAILED: Trade not found in history.")

    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    run_test()
