import requests
import json

API_URL = "http://localhost:8000"
TOKEN = "mock-token-123"

order_payload = {
    "tradingsymbol": "BANKNIFTY",
    "transaction_type": "BUY",
    "quantity": 15,  # 1 lot (Bank Nifty LOT size is 15)
    "exchange": "NSE",
    "product": "MIS",
    "order_type": "MARKET"
}

print(f"Placing BANKNIFTY Test Order at {API_URL}...")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    res = requests.post(f"{API_URL}/api/order/place", json=order_payload, headers=headers)
    print(f"Status Code: {res.status_code}")
    print(f"Response Content: {res.text}")
    
    # Try to parse JSON for better readability
    try:
        data = res.json()
        print(f"Formatted Response: {json.dumps(data, indent=4)}")
    except:
        pass
        
except Exception as e:
    print(f"Request failed: {e}")
