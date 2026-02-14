import logging
import time
from config import config

# Placeholder for Redis or File-based persistence
# In a real system, we'd use Redis keys.
# For now, we'll use a simple file marker or in-memory singleton if process is persistent (which it isn't always).
# Let's use a file marker for simplicity across processes.
KILL_SWITCH_FILE = "kill_switch.lock"

logger = logging.getLogger(__name__)

class KillSwitch:
    """
    Emergency Stop mechanism for the Trading System.
    """
    def __init__(self, broker_client=None):
        self.broker = broker_client

    def activate(self, reason="Manual Activation"):
        """
        Activates the Kill Switch:
        1. Set system state to STOPPED (File Marker).
        2. Cancel all pending orders.
        3. Attempts to liquidate positions (Optional - strict kill vs soft kill).
        """
        logger.critical(f"🛑 KILL SWITCH ACTIVATED: {reason}")
        
        # 1. Create Lock File
        with open(KILL_SWITCH_FILE, "w") as f:
            f.write(f"ACTIVATED at {time.ctime()}\nReason: {reason}")
            
        # 2. Cancel Orders
        if self.broker:
            try:
                # Assuming broker has cancel_all logic
                # self.broker.cancel_all_orders() 
                # For now, we log it as we don't have a standardized wrapper yet
                logger.critical("🛑 Pseudo-call: self.broker.cancel_all_orders()")
            except Exception as e:
                logger.error(f"Failed to cancel orders during Kill Switch: {e}")
        
    def deactivate(self):
        """
        Deactivates the Kill Switch (Manual Reset).
        """
        import os
        if os.path.exists(KILL_SWITCH_FILE):
            os.remove(KILL_SWITCH_FILE)
            logger.info("✅ Kill Switch DEACTIVATED. System resuming.")
        else:
            logger.info("Kill Switch was not active.")

    def is_active(self):
        """
        Checks if the Kill Switch is active.
        """
        import os
        return os.path.exists(KILL_SWITCH_FILE)

    def get_status(self):
        if self.is_active():
            try:
                with open(KILL_SWITCH_FILE, "r") as f:
                    details = f.read().strip()
            except: details = "Active (Unknown Reason)"
            return {"status": "KILLED", "details": details}
        return {"status": "NOMINAL", "details": "System Running"}
