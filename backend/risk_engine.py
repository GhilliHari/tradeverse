from typing import Dict, Optional

class RiskEngine:
    """
    Automated Risk Guardrails for Tradeverse.
    Enforces daily loss limits, crash protection, and position sizing.
    """
    def __init__(self, daily_loss_limit: float = 5000.0, max_position_size: float = 100000.0):
        self.daily_loss_limit = daily_loss_limit
        self.max_position_size = max_position_size
        self.current_daily_loss = 0.0
        self.circuit_breaker_active = False

    def validate_order(self, order_details: Dict) -> Dict:
        """
        Validates if an order complies with risk rules.
        """
        if self.circuit_breaker_active:
            return {"allowed": False, "reason": "Circuit breaker is ACTIVE. Trading halted."}

        if self.current_daily_loss >= self.daily_loss_limit:
            return {"allowed": False, "reason": "Daily loss limit reached."}

        order_value = order_details.get("quantity", 0) * order_details.get("price", 0)
        if order_value > self.max_position_size:
            return {"allowed": False, "reason": f"Order value ({order_value}) exceeds max position size."}

        return {"allowed": True, "reason": "Safe to proceed."}

    def update_pnl(self, realized_pnl: float):
        """
        Updates the daily PnL and checks if the loss limit is breached.
        """
        self.current_daily_loss += -realized_pnl if realized_pnl < 0 else 0
        if self.current_daily_loss >= self.daily_loss_limit:
            self.circuit_breaker_active = True

    def trigger_circuit_breaker(self, active: bool = True, reason: str = "Manual/System Trigger"):
        """
        Manually or automatically triggers/resets the circuit breaker.
        """
        self.circuit_breaker_active = active
        return {"status": "HALTED" if active else "ACTIVE", "reason": reason}

    def get_risk_status(self) -> Dict:
        """
        Returns the current status of the risk engine.
        """
        return {
            "daily_loss_limit": self.daily_loss_limit,
            "current_daily_loss": self.current_daily_loss,
            "circuit_breaker_status": "HALTED" if self.circuit_breaker_active else "NOMINAL",
            "max_position_size": self.max_position_size
        }
