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
    def __init__(self):
        self.phone = config.WHATSAPP_PHONE
        self.api_key = config.WHATSAPP_API_KEY
        self.enabled = bool(self.phone and self.api_key)
        
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

notifier = WhatsAppNotifier()
