import json
import os

with open('settings_source.json', 'r') as f:
    creds = json.load(f)

settings = {
    "ENV": "LIVE",
    "ANGEL_CLIENT_ID": creds['client_id'],
    "ANGEL_PASSWORD": creds['mpin'],
    "ANGEL_API_KEY": creds['api_key'],
    "ANGEL_TOTP_KEY": creds['totp_token'],
    "ACTIVE_BROKER": "ANGEL"
}

with open('settings.json', 'w') as f:
    json.dump(settings, f, indent=4)

print("Mapped credentials to tradeverse settings.json")
