import os
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from config import config

# Setup Logging
logger = logging.getLogger("Auth")

# Security Scheme
security = HTTPBearer()

# Initialize Firebase Admin
try:
    # Check if we have credentials file or env vars
    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin Initialized with Credentials File")
    else:
        # Attempt minimal init for development or environment-based auth (e.g. Google Cloud Run)
        # Note: In a real production apps, you'd stricter checks here
        try:
             firebase_admin.get_app()
        except ValueError:
             # App not initialized
             if config.ENV == "LIVE" and not os.getenv("MockAuth"):
                 logger.warning("Firebase Credentials missing in LIVE mode. Auth may fail.")
                 # Initialize with default for cloud run / workload identity
                 firebase_admin.initialize_app()
             else:
                 logger.info("Firebase Admin NOT initialized (Dev Mode)")

except Exception as e:
    logger.error(f"Firebase Admin Init Error: {e}")

from user_context import set_user_context

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the JWT token from Firebase.
    Returns the decoded user payload.
    """
    token = credentials.credentials
    
    user_data = None
    
    # 1. Dev Bypass / Mock Mode
    if config.ENV != "LIVE" or token == "mock-token-123":
        logger.info(f"Allowing Mock Auth for token: {token[:5]}...")
        user_data = {"uid": "mock-user-001", "email": "dev@tradeverse.ai", "name": "Dev User"}

    # 2. Verify with Firebase
    else:
        try:
            decoded_token = auth.verify_id_token(token)
            user_data = decoded_token
        except Exception as e:
            logger.error(f"Token Verification Failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    # Set Metadata Context
    if user_data:
        set_user_context(user_data['uid'])
        
    return user_data
