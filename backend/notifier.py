import httpx
import logging
import asyncio
import urllib.parse
from config import config

logger = logging.getLogger("TradeverseNotifier")

class WhatsAppNotifier:
    """
    Asynchronous WhatsApp Notifier for Tradeverse Alerts using CallMeBot.
    """
    @property
    def phone(self):
        return config.WHATSAPP_PHONE

    @property
    def api_key(self):
        return config.WHATSAPP_API_KEY

    @property
    def enabled(self):
        return bool(self.phone and self.api_key)

    def __init__(self):
        if not self.enabled:
            logger.warning("⚠️ WhatsApp Notifier disabled: Missing Phone or API Key.")
        else:
            logger.info(f"✅ WhatsApp Notifier initialized for {self.phone[:5]}***.")

    async def send_message(self, text: str):
        """Sends a message via CallMeBot WhatsApp API."""
        if not self.enabled:
            return
            
        # Clean markdown for WhatsApp (limited support)
        # CallMeBot uses simple GET requests
        encoded_text = urllib.parse.quote(text)
        url = f"https://api.callmebot.com/whatsapp.php?phone={self.phone}&text={encoded_text}&apikey={self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    logger.debug("WhatsApp message delivered.")
                else:
                    logger.error(f"❌ CallMeBot Error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")

    def notify_sync(self, text: str):
        """Synchronous wrapper for firing off messages."""
        if not self.enabled:
            return
        
        try:
            # Strip markdown stars for cleaner WhatsApp display if needed, 
            # but CallMeBot handles them somewhat.
            clean_text = text.replace("*", "*").replace("`", " ")
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_message(clean_text))
            else:
                loop.run_until_complete(self.send_message(clean_text))
        except Exception as e:
            logger.error(f"Error in WhatsApp sync notification: {e}")

class TelegramNotifier:
    """
    Asynchronous Telegram Notifier for Tradeverse Alerts.
    """
    @property
    def bot_token(self):
        return config.TELEGRAM_BOT_TOKEN

    @property
    def chat_id(self):
        return config.TELEGRAM_CHAT_ID

    @property
    def enabled(self):
        return bool(self.bot_token and self.chat_id)

    async def send_message(self, text: str):
        """Sends a message via Telegram Bot API."""
        if not self.enabled:
            return
            
        # Telegram supports basic HTML/Markdown
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.debug("Telegram message delivered.")
                else:
                    logger.error(f"❌ Telegram Error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")

class MultiNotifier:
    """
    Multiplexer for multiple notification channels.
    """
    def __init__(self):
        self.whatsapp = WhatsAppNotifier()
        self.telegram = TelegramNotifier()

    async def send_message(self, text: str):
        """Sends to all enabled channels concurrently."""
        tasks = []
        if self.whatsapp.enabled:
            tasks.append(self.whatsapp.send_message(text))
        if self.telegram.enabled:
            tasks.append(self.telegram.send_message(text))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def notify_sync(self, text: str):
        """Synchronous fire-and-forget wrapper."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_message(text))
            else:
                loop.run_until_complete(self.send_message(text))
        except Exception as e:
            logger.error(f"Error in MultiNotifier sync: {e}")

    @property
    def enabled(self):
        return self.whatsapp.enabled or self.telegram.enabled

notifier = MultiNotifier()
