import asyncio
import logging
from config import config
from notifier import notifier

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def test_multi_notifier_reactivity():
    print("Testing MultiNotifier Reactivity...")
    
    # 1. Clear config
    config.WHATSAPP_PHONE = ""
    config.WHATSAPP_API_KEY = ""
    config.TELEGRAM_BOT_TOKEN = ""
    config.TELEGRAM_CHAT_ID = ""
    
    print(f"Initial Enabled Status: {notifier.enabled} (Expected: False)")
    assert notifier.enabled is False
    
    # 2. Update WhatsApp config
    print("Enabling WhatsApp...")
    config.WHATSAPP_PHONE = "+919999999999"
    config.WHATSAPP_API_KEY = "test_wa_key"
    
    print(f"WhatsApp Enabled: {notifier.whatsapp.enabled} (Expected: True)")
    assert notifier.whatsapp.enabled is True
    print(f"Overall Enabled: {notifier.enabled} (Expected: True)")
    assert notifier.enabled is True
    
    # 3. Update Telegram config
    print("Enabling Telegram...")
    config.TELEGRAM_BOT_TOKEN = "123:ABC"
    config.TELEGRAM_CHAT_ID = "987"
    
    print(f"Telegram Enabled: {notifier.telegram.enabled} (Expected: True)")
    assert notifier.telegram.enabled is True
    
    # 4. Simulated send
    print("Simulating send to all channels...")
    # This won't actually hit APIs with real data, but verifies logic flow
    await notifier.send_message("Integration Test")
    
    print("MultiNotifier Reactivity Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_multi_notifier_reactivity())
