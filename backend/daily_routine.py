import os
import sys
import logging
import asyncio
import requests
from datetime import datetime
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TradeverseRoutine - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("maintenance.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Maintenance")

def run_lite_training():
    """Triggers the Sklearn model retraining sequence."""
    logger.info("🧠 STEP 1: Starting Neural Core Brain Re-Calibration...")
    try:
        from train_lite import train_daily_strategist, train_intraday_sniper
        train_daily_strategist()
        train_intraday_sniper()
        logger.info("✅ Brains Rebuilt and Optimized successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Training Failed: {e}")
        return False

def reload_brain():
    """Tells the live backend to reload the new joblib files from disk."""
    logger.info("🔄 STEP 2: Hot-Reloading Models into Live Memory...")
    try:
        # Assuming backend is running on default port 8000
        url = "http://localhost:8000/api/ai/reload"
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Live System reloaded with fresh weights.")
            return True
        else:
            logger.warning(f"⚠️ Reload failed (Status: {response.status_code}). Is the server running?")
    except Exception as e:
        logger.error(f"❌ Connection to Backend failed: {e}")
    return False

def rotate_audit_logs():
    """Cleans up old audit logs if they get too large (preventing disk bloat)."""
    logger.info("🧹 STEP 3: Rotating Audit Logs and Data Caches...")
    files_to_check = ["greeks_audit.csv", "backend.log"]
    limit_mb = 100
    
    for filename in files_to_check:
        if os.path.exists(filename):
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            if size_mb > limit_mb:
                logger.info(f"Rotating {filename} ({size_mb:.2f} MB)...")
                os.rename(filename, f"{filename}.old")
                # Create fresh file with header if Greek audit
                if "greeks_audit.csv" in filename:
                    with open(filename, "w") as f:
                        f.write("timestamp,symbol,ltp,regime,ce_delta,pe_delta,gamma,theta,vega,iv\n")
    logger.info("✅ Maintenance complete.")

def main_routine():
    start_time = time.time()
    logger.info("==============================================")
    logger.info(f"🚀 PEAK PERFORMANCE ROUTINE STARTING: {datetime.now()}")
    
    success = run_lite_training()
    if success:
        reload_brain()
        rotate_audit_logs()
        
    duration = time.time() - start_time
    logger.info(f"🏁 ROUTINE COMPLETED IN {duration:.2f}s")
    logger.info("==============================================")

if __name__ == "__main__":
    main_routine()
