import sys
import logging

logging.basicConfig(level=logging.INFO)

from angel_client import AngelClient
from config import config

def main():
    api_key = config.ANGEL_API_KEY
    client_id = config.ANGEL_CLIENT_ID
    password = config.ANGEL_PASSWORD
    totp_key = config.ANGEL_TOTP_KEY

    print(f"Testing login for Client ID: {client_id}")

    if not api_key or not client_id:
         print("Missing API KEY or CLIENT ID")
         return

    try:
        client = AngelClient(api_key, client_id, password, totp_key)
        print("Client initialized")
        print("Is Connected:", client.is_connected())
        if client.is_connected():
            print("Profile:", client.profile())
        else:
            print("Login error:", client.get_login_error())
    except Exception as e:
        print(f"Exception during login: {e}")

if __name__ == "__main__":
    main()
