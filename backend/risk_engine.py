from datetime import datetime, timedelta
from typing import Dict, Optional
from notifier import notifier
from kill_switch import KillSwitch
import logging

logger = logging.getLogger("RiskEngine")

class RiskEngine:
    """
    Automated Risk Guardrails for Tradeverse.
    Enforces daily loss limits, crash protection, and cool-off periods.
    """
    def __init__(self, daily_loss_limit: float = 5000.0, max_position_size: float = 100000.0):
        self.daily_loss_limit = daily_loss_limit
        self.max_position_size = max_position_size
        self.current_daily_loss = 0.0
        self.circuit_breaker_active = False
        self.kill_switch = KillSwitch()
        
        # --- NEW: Institutional Cool-off ---
        self.last_loss_time = None
        self.cool_off_duration = timedelta(minutes=30) # 30 min cool-off after a loss

    def validate_order(self, order_details: Dict) -> Dict:
        """
        Validates if an order complies with risk rules.
        """
        if self.circuit_breaker_active:
            return {"allowed": False, "reason": "Circuit breaker is ACTIVE. Trading halted."}
            
        if self.kill_switch.is_active():
             return {"allowed": False, "reason": "KILL SWITCH ACTIVE. ALL TRADING STOPPED."}

        # Check Cool-off Period
        if self.last_loss_time:
            time_since_loss = datetime.now() - self.last_loss_time
            if time_since_loss < self.cool_off_duration:
                remaining = self.cool_off_duration - time_since_loss
                mins = int(remaining.total_seconds() // 60)
                return {
                    "allowed": False, 
                    "reason": f"COOL-OFF ACTIVE: Revenge trade protection in effect. Re-locks in {mins}m."
                }

        if self.current_daily_loss >= self.daily_loss_limit:
            return {"allowed": False, "reason": "Daily loss limit reached."}

        # --- NEW: EOD Trading Block ---
        now = datetime.now()
        if now.hour == 15 and now.minute >= 15:
             return {"allowed": False, "reason": "MARKET CLOSING: New entries blocked after 3:15 PM."}

        order_value = order_details.get("quantity", 0) * order_details.get("price", 0)

        if order_value > self.max_position_size:
            return {"allowed": False, "reason": f"Order value ({order_value}) exceeds max position size."}

        return {"allowed": True, "reason": "Safe to proceed."}

    def update_pnl(self, realized_pnl: float):
        """
        Updates the daily PnL and checks if the loss limit is breached.
        Also triggers a cool-off period if a significant loss occurs.
        """
        if realized_pnl < 0:
            loss_amt = abs(realized_pnl)
            self.current_daily_loss += loss_amt
            
            # Trigger Cool-off if loss > 1% of max position (significant trade loss)
            if loss_amt > (self.max_position_size * 0.01):
                self.last_loss_time = datetime.now()
                logger.warning(f"❄️ COOL-OFF TRIGGERED: Post-loss tilt protection active for 30m.")
                notifier.notify_sync(f"❄️ *COOL-OFF*: Post-loss protection active. New entries paused for 30m.")

        if self.current_daily_loss >= self.daily_loss_limit:
            self.circuit_breaker_active = True
            notifier.notify_sync(f"🚫 *RISK BREACH*: Daily Loss Limit Reached (₹{self.current_daily_loss:.2f}). Trading Halted.")

    def trigger_circuit_breaker(self, active: bool = True, reason: str = "Manual/System Trigger"):
        """
        Manually or automatically triggers/resets the circuit breaker.
        """
        self.circuit_breaker_active = active
        status = "HALTED" if active else "ACTIVE"
        notifier.notify_sync(f"⚡ *CIRCUIT BREAKER*: {status}\nReason: {reason}")
        return {"status": status, "reason": reason}

    def get_risk_status(self) -> Dict:
        """
        Returns the current status of the risk engine.
        """
        cool_off_active = False
        remaining_str = "0m"
        if self.last_loss_time:
            time_since = datetime.now() - self.last_loss_time
            if time_since < self.cool_off_duration:
                cool_off_active = True
                remaining = self.cool_off_duration - time_since
                remaining_str = f"{int(remaining.total_seconds() // 60)}m"

        return {
            "daily_loss_limit": self.daily_loss_limit,
            "current_daily_loss": self.current_daily_loss,
            "circuit_breaker_status": "HALTED" if self.circuit_breaker_active else "NOMINAL",
            "max_position_size": self.max_position_size,
            "cool_off_active": cool_off_active,
            "cool_off_remaining": remaining_str
        }

