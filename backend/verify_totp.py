import pyotp
import base64

secret = "G2757JBA3NMMYCF6NYA2IMWG2E"
print(f"Secret: {secret}")
print(f"Length: {len(secret)}")

try:
    clean_totp = secret.replace(" ", "").strip()
    missing_padding = len(clean_totp) % 8
    if missing_padding:
        clean_totp += '=' * (8 - missing_padding)
    print(f"Clean (padded): {clean_totp}")
    base64.b32decode(clean_totp, casefold=True)
    print("Base32 Decode: SUCCESS")
    
    totp = pyotp.TOTP(secret.replace(" ", "").strip())
    print(f"TOTP Code: {totp.now()}")
except Exception as e:
    print(f"Error: {e}")

# Check characters
base32_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
for i, char in enumerate(secret):
    if char.upper() not in base32_alphabet:
        print(f"Invalid character at index {i}: '{char}'")
