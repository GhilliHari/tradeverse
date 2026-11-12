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
    def __init__(self, daily_loss_limit: Optional[float] = None, max_position_size: Optional[float] = None, max_open_positions: Optional[int] = None):
        from config import config
        self.daily_loss_limit = float(daily_loss_limit if daily_loss_limit is not None else getattr(config, "DAILY_LOSS_LIMIT", 1000.0))
        self.max_position_size = float(max_position_size if max_position_size is not None else getattr(config, "MAX_POSITION_SIZE", 10000.0))
        self.max_open_positions = int(max_open_positions if max_open_positions is not None else getattr(config, "MAX_OPEN_POSITIONS", 1))
        self.current_daily_loss = 0.0
        self.circuit_breaker_active = False
        self.kill_switch = KillSwitch()
        self.processed_trade_ids = set()
        
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
        if now.hour == 15 and now.minute >= 15 and not order_details.get("is_exit"):
             return {"allowed": False, "reason": "MARKET CLOSING: New entries blocked after 3:15 PM."}

        qty = float(order_details.get("quantity") or 0)
        price = float(order_details.get("price") or 0.0)
        if qty <= 0:
            return {"allowed": False, "reason": "Order quantity must be greater than 0."}

        if order_details.get("require_live_price") and price <= 0.0:
            return {"allowed": False, "reason": "Live order rejected: verified broker LTP is 0.0 (untradable or unmapped contract)."}

        open_count = int(order_details.get("open_positions_count") or 0)
        if not order_details.get("is_exit") and open_count >= self.max_open_positions:
            return {"allowed": False, "reason": f"Max open positions limit ({self.max_open_positions}) reached."}

        order_value = qty * price

        if order_value > self.max_position_size:
            return {"allowed": False, "reason": f"Order value ({order_value}) exceeds max position size."}

        return {"allowed": True, "reason": "Safe to proceed."}

    def update_pnl(self, realized_pnl: float, trade_id: Optional[str] = None):
        """
        Updates the daily PnL and checks if the loss limit is breached.
        Also triggers a cool-off period if a significant loss occurs.
        """
        if trade_id:
            if trade_id in self.processed_trade_ids:
                return
            self.processed_trade_ids.add(trade_id)
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
            "max_open_positions": self.max_open_positions,
            "cool_off_active": cool_off_active,
            "cool_off_remaining": remaining_str
        }

