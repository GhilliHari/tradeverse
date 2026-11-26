
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
    from pathlib import Path as _Path
    load_dotenv(_Path(__file__).resolve().parent / ".env")
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
    
    # API Keys (Loaded strictly from git-ignored .env / environment variables to prevent GitHub leak auto-revocation)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    REDIS_URL = os.getenv("REDIS_URL", "")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")
    
    # Angel Broking Primary Account Keys (Account #1)
    ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
    ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
    ANGEL_TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")
    ANGEL_ACCOUNT_NAME = os.getenv("ANGEL_ACCOUNT_NAME", "Primary Account (Hari)")

    # Angel Broking Secondary Copy-Trade Account Keys (Account #2 — loaded strictly from git-ignored .env)
    ANGEL2_CLIENT_ID = os.getenv("ANGEL2_CLIENT_ID", "")
    ANGEL2_PASSWORD = os.getenv("ANGEL2_PASSWORD", "")
    ANGEL2_API_KEY = os.getenv("ANGEL2_API_KEY", "")
    ANGEL2_TOTP_KEY = os.getenv("ANGEL2_TOTP_KEY", "")
    ANGEL2_NAME = os.getenv("ANGEL2_NAME", "Account 2")
    ANGEL2_ACTIVE = os.getenv("ANGEL2_ACTIVE", "true").lower() in ("true", "1", "yes")

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
            "GEMINI_API_KEY": "" if os.getenv("GEMINI_API_KEY") else self.GEMINI_API_KEY,
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
        Dynamically merges git-ignored .env accounts (Primary ANGEL_* + Secondary ANGEL2_*, ANGEL3_*)
        with any explicit ANGEL_ACCOUNTS entries without ever writing secrets to git-tracked settings.json.
        """
        # Re-read .env dynamically so newly added accounts activate without code changes
        try:
            from dotenv import load_dotenv
            from pathlib import Path as _Path
            load_dotenv(_Path(__file__).resolve().parent / ".env", override=True)
        except Exception:
            pass

        accounts_out = []
        seen_ids = set()

        # 1. Primary Account (ANGEL_*)
        p_cid = (os.getenv("ANGEL_CLIENT_ID") or self.ANGEL_CLIENT_ID or "").strip()
        p_key = (os.getenv("ANGEL_API_KEY") or self.ANGEL_API_KEY or "").strip()
        p_pwd = (os.getenv("ANGEL_PASSWORD") or self.ANGEL_PASSWORD or "").strip()
        p_totp = (os.getenv("ANGEL_TOTP_KEY") or self.ANGEL_TOTP_KEY or "").strip()
        p_name = (os.getenv("ANGEL_ACCOUNT_NAME") or getattr(self, "ANGEL_ACCOUNT_NAME", "Doss") or "Doss").strip()
        if p_cid and p_key:
            accounts_out.append({
                "account_id": p_cid,
                "name": p_name,
                "client_id": p_cid,
                "password": p_pwd,
                "api_key": p_key,
                "totp_key": p_totp,
                "active": True,
            })
            seen_ids.add(p_cid)

        # 2. Additional Accounts from .env (ANGEL2_*, ANGEL3_*, ANGEL4_*)
        for idx in (2, 3, 4):
            prefix = f"ANGEL{idx}_"
            cid = (os.getenv(f"{prefix}CLIENT_ID") or "").strip()
            akey = (os.getenv(f"{prefix}API_KEY") or "").strip()
            pwd = (os.getenv(f"{prefix}PASSWORD") or "").strip()
            totp = (os.getenv(f"{prefix}TOTP_KEY") or "").strip()
            aname = (os.getenv(f"{prefix}NAME") or f"Account {idx}").strip()
            is_act = (os.getenv(f"{prefix}ACTIVE", "true") or "true").strip().lower() in ("true", "1", "yes")
            if cid and akey and cid not in seen_ids:
                accounts_out.append({
                    "account_id": cid,
                    "name": aname,
                    "client_id": cid,
                    "password": pwd,
                    "api_key": akey,
                    "totp_key": totp,
                    "active": is_act,
                })
                seen_ids.add(cid)

        # 3. Merge any extra runtime ANGEL_ACCOUNTS entries not already covered
        extra_accounts = getattr(self, "ANGEL_ACCOUNTS", None)
        if extra_accounts and isinstance(extra_accounts, list):
            for acc in extra_accounts:
                cid = (acc.get("client_id") or "").strip()
                if cid and cid not in seen_ids:
                    accounts_out.append(acc)
                    seen_ids.add(cid)

        return accounts_out

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
                        # Never overwrite an explicit GEMINI_API_KEY from .env with a stale/empty settings.json value
                        if k == "GEMINI_API_KEY" and os.getenv("GEMINI_API_KEY"):
                            continue
                        # Explicit settings.json takes precedence over stale cloud env vars when non-empty
                        if v not in ("", None):
                            setattr(self, k, v)
                            logger.info(f"Loaded {k} from {settings_path.name}")
            except Exception as e:
                logger.debug(f"Could not load settings.json: {e}")

config = Config()
config.load()
