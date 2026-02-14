import requests
import json

API_URL = "http://localhost:8000"
TOKEN = "mock-token-123"

# Load credentials from source
with open('settings_source.json', 'r') as f:
    creds = json.load(f)

payload = {
    "env": "LIVE",
    "active_broker": "ANGEL",
    "angel_client_id": creds['client_id'],
    "angel_api_key": creds['api_key'],
    "angel_totp_key": creds['totp_token'],
    "angel_password": creds['mpin']
}

print(f"Updating settings at {API_URL}...")
try:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    res = requests.post(f"{API_URL}/api/settings/update", json=payload, headers=headers)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Request failed: {e}")
