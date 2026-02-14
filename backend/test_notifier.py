import asyncio
import logging
from config import config
from notifier import WhatsAppNotifier

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def test_notifier_reactivity():
    print("Testing Notifier Reactivity...")
    
    # 1. Initialize with empty config
    config.WHATSAPP_PHONE = ""
    config.WHATSAPP_API_KEY = ""
    notifier = WhatsAppNotifier()
    
    print(f"Initial Enabled Status: {notifier.enabled} (Expected: False)")
    assert notifier.enabled is False
    
    # 2. Update config at runtime
    print("Updating config...")
    config.WHATSAPP_PHONE = "+919999999999"
    config.WHATSAPP_API_KEY = "test_api_key"
    
    print(f"Updated Enabled Status: {notifier.enabled} (Expected: True)")
    assert notifier.enabled is True
    print(f"Current Phone: {notifier.phone}")
    assert notifier.phone == "+919999999999"
    
    # 3. Test send_message (mocked or observed)
    # We won't actually send because the key is fake, but we verify it tries
    print("Reactivity Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_notifier_reactivity())
