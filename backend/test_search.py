from angel_client import AngelClient
from config import config
import logging

logging.basicConfig(level=logging.INFO)

def test_search():
    client = AngelClient(
        api_key=config.ANGEL_API_KEY,
        client_id=config.ANGEL_CLIENT_ID,
        password=config.ANGEL_PASSWORD,
        totp_key=config.ANGEL_TOTP_KEY
    )
    
    if client.is_connected():
        print("Connected! Searching for SBIN...")
        results = client.search_scrip("SBIN")
        print(f"Results: {results}")
    else:
        print("Failed to connect.")

if __name__ == "__main__":
    test_search()
