
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    # Environment: MOCK or LIVE
    ENV = os.getenv("TRADEVERSE_ENV", "MOCK").upper()
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
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
            "TRADING_MODE": self.TRADING_MODE
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
                        setattr(self, k, v)
            except:
                pass

config = Config()
config.load()
