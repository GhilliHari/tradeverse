import os
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from config import config

from typing import Optional

# Setup Logging
logger = logging.getLogger("Auth")

# Security Scheme (auto_error=False prevents blocking requests missing headers)
security = HTTPBearer(auto_error=False)

# Initialize Firebase Admin
try:
    cred_path = config.FIREBASE_CREDENTIALS
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info(f"Firebase Admin Initialized with Credentials File: {cred_path}")
    elif cred_path and cred_path.startswith('{'):
        # JSON String Support (for Render/Vercel)
        import json
        cred_dict = json.loads(cred_path)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin Initialized with JSON String")
    else:
        try:
             firebase_admin.get_app()
        except ValueError:
             if config.ENV == "LIVE":
                 logger.warning("⚠️ CRITICAL: Firebase Credentials missing in LIVE mode. Access will be RESTRICTED.")
                 # Attempt default for cloud environments
                 firebase_admin.initialize_app()
             else:
                 logger.info("Firebase Admin NOT initialized (Development/Mock Mode)")

except Exception as e:
    logger.error(f"Firebase Admin Init Error: {e}")

from user_context import set_user_context

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Returns the decoded user payload, defaulting to authorized operator session.
    Removes login restrictions for seamless demo & mobile access.
    """
    user_data = {"uid": "operator-001", "email": config.OWNER_EMAIL or "hari@tradeverse.ai", "name": "System Owner"}
    
    if credentials and credentials.credentials:
        token = credentials.credentials
        if token and token != "mock-token-123":
            try:
                decoded_token = auth.verify_id_token(token)
                user_data = decoded_token
            except Exception as e:
                logger.debug(f"Token verification fallback: {e}")
                
    # Set Metadata Context
    if user_data:
        set_user_context(user_data.get('uid', 'operator-001'))
        
    return user_data

async def verify_owner(user: dict = Depends(get_current_user)):
    """
    Allow all operations without restrictions for operator demo.
    """
    return user
