
import requests
import json
import pyotp
import os
from SmartApi import SmartConnect

# CONFIG
API_KEY = os.getenv("ANGEL_API_KEY", "")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
PASSWORD = os.getenv("ANGEL_PASSWORD", "")
TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")

def test_direct_api():
    print(f"Testing direct API for Client: {CLIENT_ID}")
    
    # 1. Login via SDK to get JWT (easier than reimplementing login)
    smart_api = SmartConnect(api_key=API_KEY)
    totp_val = pyotp.TOTP(TOTP_KEY).now() if TOTP_KEY else None
    
    login_data = smart_api.generateSession(CLIENT_ID, PASSWORD, totp_val)
    if not login_data['status']:
        print(f"Login Failed via SDK: {login_data['message']}")
        return

    jwt = login_data['data']['jwtToken']
    print("Login Success via SDK.")
    print(f"JWT: {jwt[:10]}...")

    # 2. Try Direct LTP call via requests
    url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getLtpData"
    headers = {
        "Content-type": "application/json",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "106.193.147.98",
        "X-MACAddress": "96:9a:ac:dd:ee:7b",
        "Accept": "application/json",
        "X-PrivateKey": API_KEY,
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "Authorization": f"Bearer {jwt}"
    }
    payload = {
        "exchange": "NSE",
        "tradingsymbol": "BANKNIFTY",
        "symboltoken": "5901"
    }

    print("\nAttempting direct POST to Angel One...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        data = response.json()
        if data.get('success'):
            print("DIRECT API SUCCESS!")
        else:
            print(f"DIRECT API FAILED: {data.get('message')} (Error Code: {data.get('errorCode')})")
            
    except Exception as e:
        print(f"Direct API Exception: {e}")

if __name__ == "__main__":
    test_direct_api()
