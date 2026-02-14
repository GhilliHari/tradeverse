import redis
import json
import os

# Connect to Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    print(f"Connected to Redis at {REDIS_URL}")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")
    exit(1)

# Load credentials from source
with open('settings_source.json', 'r') as f:
    creds = json.load(f)

# Guest User ID (from auth_middleware.py bypass)
USER_ID = "mock-user-001"
SETTINGS_KEY = f"user:{USER_ID}:settings"

# Prepare settings
settings = {
    "ENV": "LIVE",
    "ANGEL_CLIENT_ID": creds['client_id'],
    "ANGEL_PASSWORD": creds['mpin'],
    "ANGEL_API_KEY": creds['api_key'],
    "ANGEL_TOTP_KEY": creds['totp_token'],
    "ACTIVE_BROKER": "ANGEL"
}

# Save to Redis
r.set(SETTINGS_KEY, json.dumps(settings))
print(f"✅ Successfully injected LIVE credentials for {USER_ID} into {SETTINGS_KEY}")

# Also update global settings.json for safety
with open('settings.json', 'w') as f:
    json.dump(settings, f, indent=4)
print("✅ Updated local settings.json")
