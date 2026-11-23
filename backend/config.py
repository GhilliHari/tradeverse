
import os
import time as _time

# Enforce Indian Standard Time (IST) for NSE Market Hours across all Cloud/Docker environments
os.environ.setdefault("TZ", "Asia/Kolkata")
if hasattr(_time, "tzset"):
    try:
        _time.tzset()
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import logging
logger = logging.getLogger("Config")

class Config:
    # IP Protection: Master Operator ID
    OWNER_EMAIL = os.getenv("OWNER_EMAIL", "Hari@tradeverse.ai")

    # Environment: MOCK or LIVE (Defaults to LIVE for Angel One Cloud Trading)
    ENV = os.getenv("TRADEVERSE_ENV", "LIVE").upper()
    
    # Offline Autonomous Cloud Mode (Runs 24/7 even when iMac / Browser is OFF)
    OFFLINE_AUTONOMOUS_MODE = os.getenv("OFFLINE_AUTONOMOUS_MODE", "true").lower() in ("true", "1", "yes")
    
    # API Keys (Defaults to embedded operator key / GraphRAG fallback if not set in env)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAMxry7kyw7svsZumX6_hu7aGELVHamkm0")
    REDIS_URL = os.getenv("REDIS_URL", "")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")
    
    # Angel Broking Keys
    ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
    ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
    ANGEL_TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")

    # Multi-Account Copy-Trading Configuration: list of dicts with keys:
    # {"account_id", "name", "client_id", "password", "api_key", "totp_key", "active"}
    ANGEL_ACCOUNTS = []

    # Active Broker: Default to ANGEL
    ACTIVE_BROKER = os.getenv("ACTIVE_BROKER", "ANGEL").upper()
    
    # Risk Settings
    DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", 1000.0))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", 10000.0))
    MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", 1))
    
    # WhatsApp Notifications (CallMeBot)
    WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")
    WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
    
    # Telegram Notifications (Bot API)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Trading Mode: MANUAL or AUTO (Defaults to AUTO for headless cloud execution)
    TRADING_MODE = os.getenv("TRADING_MODE", "AUTO").upper()

    def save(self):
        import json
        from pathlib import Path
        data = {
            "ENV": self.ENV,
            "OFFLINE_AUTONOMOUS_MODE": getattr(self, "OFFLINE_AUTONOMOUS_MODE", True),
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "ANGEL_CLIENT_ID": self.ANGEL_CLIENT_ID,
            "ANGEL_PASSWORD": self.ANGEL_PASSWORD,
            "ANGEL_API_KEY": self.ANGEL_API_KEY,
            "ANGEL_TOTP_KEY": self.ANGEL_TOTP_KEY,
            "ACTIVE_BROKER": self.ACTIVE_BROKER,
            "TRADING_MODE": self.TRADING_MODE,
            "DAILY_LOSS_LIMIT": getattr(self, "DAILY_LOSS_LIMIT", 1000.0),
            "MAX_POSITION_SIZE": getattr(self, "MAX_POSITION_SIZE", 10000.0),
            "MAX_OPEN_POSITIONS": getattr(self, "MAX_OPEN_POSITIONS", 1),
            "WHATSAPP_PHONE": self.WHATSAPP_PHONE,
            "WHATSAPP_API_KEY": self.WHATSAPP_API_KEY,
            "TELEGRAM_BOT_TOKEN": self.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": self.TELEGRAM_CHAT_ID,
            "ANGEL_ACCOUNTS": getattr(self, "ANGEL_ACCOUNTS", [])
        }
        settings_path = Path(__file__).resolve().parent / "settings.json"
        with open(settings_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_angel_accounts(self):
        """
        Returns list of configured Angel One accounts for copy-trading.
        Falls back to primary single account if ANGEL_ACCOUNTS is not populated.
        """
        accounts = getattr(self, "ANGEL_ACCOUNTS", None)
        if accounts and isinstance(accounts, list) and len(accounts) > 0:
            return accounts
        if self.ANGEL_CLIENT_ID:
            return [{
                "account_id": self.ANGEL_CLIENT_ID,
                "name": "Primary Account",
                "client_id": self.ANGEL_CLIENT_ID,
                "password": self.ANGEL_PASSWORD,
                "api_key": self.ANGEL_API_KEY,
                "totp_key": self.ANGEL_TOTP_KEY,
                "active": True
            }]
        return []

    def load(self):
        import json
        from pathlib import Path
        settings_path = Path(__file__).resolve().parent / "settings.json"
        if not settings_path.exists() and os.path.exists("settings.json"):
            settings_path = Path("settings.json")
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        # Explicit settings.json takes precedence over stale cloud env vars when non-empty
                        if v not in ("", None):
                            setattr(self, k, v)
                            logger.info(f"Loaded {k} from {settings_path.name}")
            except Exception as e:
                logger.debug(f"Could not load settings.json: {e}")

config = Config()
config.load()
