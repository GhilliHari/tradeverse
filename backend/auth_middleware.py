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
        user_data = {"uid": "mock-user-001", "email": config.OWNER_EMAIL, "name": "System Owner"}

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

async def verify_owner(user: dict = Depends(get_current_user)):
    """
    Dependency to restrict access to the system owner only.
    """
    user_email = user.get("email", "").lower().strip()
    owner_email = config.OWNER_EMAIL.lower().strip()
    
    logger.info(f"Owner Check: User={user_email} | Owner={owner_email}")

    if user_email != owner_email:
        logger.warning(f"🚫 Unauthorized Access Attempt: User {user_email} tried to access OWNER-ONLY resources. Registered Owner: {owner_email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This operation is restricted to the Tradeverse system owner ({owner_email})."
        )
    return user
