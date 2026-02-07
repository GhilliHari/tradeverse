
import logging
import os
from SmartApi import SmartConnect
import pyotp

# Simulate enough of config to run
class MockConfig:
    ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
    ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
    ANGEL_TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")

cfg = MockConfig()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugSDK")

def debug_angel():
    if not cfg.ANGEL_API_KEY:
        print("Error: ANGEL_API_KEY not set in env")
        return

    smart_api = SmartConnect(api_key=cfg.ANGEL_API_KEY)
    
    totp_val = None
    if cfg.ANGEL_TOTP_KEY:
        totp_val = pyotp.TOTP(cfg.ANGEL_TOTP_KEY).now()
        print(f"Generated TOTP: {totp_val}")

    print("Attempting generateSession...")
    data = smart_api.generateSession(cfg.ANGEL_CLIENT_ID, cfg.ANGEL_PASSWORD, totp_val)
    
    if data['status']:
        print("Login Success!")
        jwt = data['data']['jwtToken']
        print(f"JWT Token (Length {len(jwt)}): {jwt[:10]}...")
        
        # LOG ALL ATTRIBUTES OF smart_api TO SEE WHERE TOKEN IS STORED
        print("\n--- Inspecting smart_api object properties ---")
        for attr in dir(smart_api):
            if not attr.startswith("__") and not callable(getattr(smart_api, attr)):
                val = getattr(smart_api, attr)
                print(f"{attr}: {val}")
        
        # Test LTP call
        print("\nAttempting LTP call...")
        try:
            res = smart_api.ltpData("NSE", "BANKNIFTY", "5901")
            print(f"LTP Result: {res}")
        except Exception as e:
            print(f"LTP Exception: {e}")
    else:
        print(f"Login Failed: {data['message']}")

if __name__ == "__main__":
    debug_angel()
