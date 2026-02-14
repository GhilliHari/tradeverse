
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import logging
logger = logging.getLogger("Config")

class Config:
    # Environment: MOCK or LIVE
    ENV = os.getenv("TRADEVERSE_ENV", "MOCK").upper()
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAMxry7kyw7svsZumX6_hu7aGELVHamkm0")
    REDIS_URL = os.getenv("REDIS_URL", "")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "")
    
    # Angel Broking Keys
    ANGEL_CLIENT_ID = os.getenv("ANGEL_CLIENT_ID", "")
    ANGEL_PASSWORD = os.getenv("ANGEL_PASSWORD", "")
    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY", "")
    ANGEL_TOTP_KEY = os.getenv("ANGEL_TOTP_KEY", "")

    # Active Broker: Default to ANGEL
    ACTIVE_BROKER = os.getenv("ACTIVE_BROKER", "ANGEL").upper()
    
    # Risk Settings
    DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", 10000.0))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", 200000.0))
    
    # WhatsApp Notifications (CallMeBot)
    WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")
    WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
    
    # Telegram Notifications (Bot API)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Trading Mode: MANUAL or AUTO
    TRADING_MODE = os.getenv("TRADING_MODE", "MANUAL").upper()

    def save(self):
        import json
        data = {
            "ENV": self.ENV,
            "ANGEL_CLIENT_ID": self.ANGEL_CLIENT_ID,
            "ANGEL_PASSWORD": self.ANGEL_PASSWORD,
            "ANGEL_API_KEY": self.ANGEL_API_KEY,
            "ANGEL_TOTP_KEY": self.ANGEL_TOTP_KEY,
            "ACTIVE_BROKER": self.ACTIVE_BROKER,
            "TRADING_MODE": self.TRADING_MODE,
            "WHATSAPP_PHONE": self.WHATSAPP_PHONE,
            "WHATSAPP_API_KEY": self.WHATSAPP_API_KEY,
            "TELEGRAM_BOT_TOKEN": self.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": self.TELEGRAM_CHAT_ID
        }
        with open("settings.json", "w") as f:
            json.dump(data, f)

    def load(self):
        import json
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        # ONLY overwrite if not already set by Environment Variables
                        # This ensures cloud-configured vars (Render/Heroku/Vercel) take precedence
                        env_key = f"TRADEVERSE_{k}" if k == "ENV" else k
                        if not os.getenv(env_key):
                            setattr(self, k, v)
                            logger.info(f"Loaded {k} from settings.json")
            except Exception as e:
                logger.debug(f"Could not load settings.json: {e}")

config = Config()
config.load()
