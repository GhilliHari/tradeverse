
import time
import logging
import json
from redis_manager import redis_client

logger = logging.getLogger("HeartbeatMonitor")

class HeartbeatMonitor:
    def __init__(self):
        self.redis = redis_client
        self.TIMEOUT_SECONDS = 30
    
    def record_heartbeat(self, user_id: str):
        """
        Updates the heartbeat timestamp for a user.
        """
        key = f"user:{user_id}:heartbeat"
        self.redis.set(key, int(time.time()), ex=60) # Expire after 60s to auto-clean inactive users
        # logger.debug(f"Heartbeat received for {user_id}")

    def check_watchdog(self):
        """
        Checks all active heartbeat keys. 
        If a user has AUTO mode enabled but no recent heartbeat, revert to MANUAL,
        UNLESS OFFLINE_AUTONOMOUS_MODE is enabled (for 24/7 Cloud Autonomous Trading when iMac is OFF).
        """
        from config import config
        if getattr(config, "OFFLINE_AUTONOMOUS_MODE", True):
            # In 24/7 Cloud Offline Mode, the server trades autonomously without requiring an open browser tab
            return

        active_users = self.redis.smembers("set:active_auto_users")
        
        for user_id in active_users:
            hb_key = f"user:{user_id}:heartbeat"
            last_beat = self.redis.get(hb_key)
            
            now = int(time.time())
            
            if not last_beat or (now - int(last_beat) > self.TIMEOUT_SECONDS):
                logger.critical(f"🚨 DEAD MAN SWITCH TRIGGERED FOR {user_id} 🚨 - Last Signal: {last_beat}")
                self._emergency_stop(user_id)

    def _emergency_stop(self, user_id: str):
        """
        Reverts user to MANUAL mode and logs the event.
        """
        settings_key = f"user:{user_id}:settings"
        data = self.redis.get(settings_key)
        if data:
            settings = json.loads(data)
            if settings.get("TRADING_MODE") == "AUTO":
                settings["TRADING_MODE"] = "MANUAL"
                self.redis.set(settings_key, json.dumps(settings))
                
                # Update the active set
                self.redis.srem("set:active_auto_users", user_id)
                logger.info(f"User {user_id} reverted to MANUAL mode due to signal loss.")

monitor = HeartbeatMonitor()
