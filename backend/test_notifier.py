import asyncio
import logging
from notifier import WhatsAppNotifier
from config import config

logging.basicConfig(level=logging.INFO)

async def test_notifier():
    print("--- Testing WhatsApp Notifier ---")
    # Mocking config for verification
    config.WHATSAPP_PHONE = "+910000000000"
    config.WHATSAPP_API_KEY = "MOCK_KEY"
    
    test_notifier = WhatsAppNotifier()
    
    print("Testing async send_message (expecting log error 404/401 if actually sent with mock key)...")
    await test_notifier.send_message("Test WhatsApp Message from Tradeverse Verification Script")
    
    print("Testing sync notify_sync...")
    test_notifier.notify_sync("Test Sync WhatsApp Message")
    
    print("Wait for async tasks to settle...")
    await asyncio.sleep(2)
    print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_notifier())
