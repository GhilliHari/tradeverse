"""
Smart Execution Engine for Tradeverse
Institutional-grade order execution with:
- Limit Order Chasing (nudging limit price towards market up to a strict slippage ceiling)
- Passive Spread Capture
- Slippage Guard & Microstructure Protection
- Sequential Basket Execution with Margin Lock (Hedge Leg First)
- Execution Telemetry (Slippage points, INR impact, latency ms)
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("SmartExecutionEngine")


class SmartExecutionEngine:
    def __init__(self, broker=None, notifier=None):
        self.broker = broker
        self.notifier = notifier
        self.execution_audit_log: List[Dict] = []

    def set_broker(self, broker):
        self.broker = broker

    async def execute_smart_order(
        self,
        order_request: Dict[str, Any],
        broker=None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Executes an order using smart limit order chasing to prevent market order slippage.
        """
        active_broker = broker or self.broker
        if not active_broker:
            raise ValueError("No active broker client available for execution.")

        start_time = time.time()
        tradingsymbol = order_request.get("tradingsymbol", "")
        exchange = order_request.get("exchange", "NFO")
        tx_type = order_request.get("transaction_type", "BUY").upper()
        quantity = int(order_request.get("quantity", 1))
        product = order_request.get("product", "MIS")
        max_slippage_pct = float(order_request.get("max_slippage_pct", 0.006))  # 0.6% max slippage
        chase_steps = int(order_request.get("chase_steps", 3))
        step_wait_sec = float(order_request.get("step_wait_sec", 1.5))
        mode = order_request.get("mode", "SMART_LIMIT_CHASE")

        # 1. Fetch current market price
        ltp = await self._fetch_live_ltp(active_broker, exchange, tradingsymbol)
        ref_price = float(order_request.get("target_price") or ltp or 100.0)
        if ref_price <= 0:
            ref_price = ltp if ltp > 0 else 100.0

        max_slippage_pts = max(1.0, round(ref_price * max_slippage_pct, 2))
        worst_acceptable_price = round(
            ref_price + max_slippage_pts if tx_type == "BUY" else ref_price - max_slippage_pts,
            1
        )

        logger.info(
            f"⚡ [SmartExec] Starting {mode} for {tradingsymbol} ({tx_type} x {quantity}). "
            f"Ref Price: ₹{ref_price:.2f}, Max Slippage: ±₹{max_slippage_pts:.2f} (Worst: ₹{worst_acceptable_price:.2f})"
        )

        # 2. Check for Mock / Simulated Broker
        is_mock = self._is_mock_broker(active_broker)
        if is_mock:
            return await self._execute_mock_smart_fill(
                order_request=order_request,
                ref_price=ref_price,
                worst_acceptable_price=worst_acceptable_price,
                start_time=start_time,
                user_id=user_id
            )

        # 3. Live Execution: Step 1 Initial Limit Placement
        initial_offset = round(ref_price * 0.001, 1)  # 0.1% passive buffer
        current_limit_price = round(
            (ref_price - initial_offset) if tx_type == "BUY" else (ref_price + initial_offset),
            1
        )
        current_limit_price = max(0.5, current_limit_price)

        placed_order_id = None
        fill_price = None
        status = "OPEN"
        attempts_taken = 0

        try:
            placed_order_id = active_broker.place_order(
                variety="NORMAL",
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=tx_type,
                quantity=quantity,
                product=product,
                order_type="LIMIT",
                price=current_limit_price
            )
            attempts_taken = 1
            logger.info(f"⚡ [SmartExec] Initial Limit Order placed: ID {placed_order_id} @ ₹{current_limit_price:.2f}")

            # Chase loop
            for step in range(chase_steps):
                await asyncio.sleep(step_wait_sec)

                order_status_info = await self._check_order_status(active_broker, placed_order_id)
                status = order_status_info.get("status", "OPEN").upper()

                if status in ["COMPLETE", "FILLED"]:
                    fill_price = float(order_status_info.get("average_price") or current_limit_price)
                    logger.info(f"✅ [SmartExec] Order {placed_order_id} FILLED at ₹{fill_price:.2f} (Step {step + 1})")
                    break

                if status in ["REJECTED", "CANCELLED"]:
                    logger.warning(f"❌ [SmartExec] Order {placed_order_id} was {status}: {order_status_info.get('reason')}")
                    break

                if step < chase_steps - 1 and mode == "SMART_LIMIT_CHASE":
                    nudge_fraction = (step + 1) / chase_steps
                    if tx_type == "BUY":
                        new_price = round(ref_price + (max_slippage_pts * nudge_fraction), 1)
                        new_price = min(new_price, worst_acceptable_price)
                    else:
                        new_price = round(ref_price - (max_slippage_pts * nudge_fraction), 1)
                        new_price = max(new_price, worst_acceptable_price)

                    if new_price != current_limit_price:
                        logger.info(
                            f"🔄 [SmartExec] Nudging Order {placed_order_id} from ₹{current_limit_price:.2f} -> ₹{new_price:.2f} "
                            f"(Step {step + 2}/{chase_steps})"
                        )
                        current_limit_price = new_price
                        attempts_taken += 1
                        await self._modify_order_safe(
                            broker=active_broker,
                            order_id=placed_order_id,
                            exchange=exchange,
                            tradingsymbol=tradingsymbol,
                            transaction_type=tx_type,
                            quantity=quantity,
                            product=product,
                            price=current_limit_price
                        )

            if status not in ["COMPLETE", "FILLED"]:
                final_check = await self._check_order_status(active_broker, placed_order_id)
                status = final_check.get("status", "OPEN").upper()
                if status in ["COMPLETE", "FILLED"]:
                    fill_price = float(final_check.get("average_price") or current_limit_price)

            if status not in ["COMPLETE", "FILLED"]:
                logger.warning(f"🛑 [SmartExec] Order {placed_order_id} unfilled after {chase_steps} steps. Cancelling.")
                await self._cancel_order_safe(active_broker, placed_order_id)
                status = "CANCELLED_SLIPPAGE_PROTECTED"

        except Exception as e:
            logger.error(f"❌ [SmartExec] Execution Error: {e}")
            if placed_order_id:
                await self._cancel_order_safe(active_broker, placed_order_id)
            return {
                "status": "ERROR",
                "error": str(e),
                "tradingsymbol": tradingsymbol,
                "quantity": quantity
            }

        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        actual_fill = fill_price or current_limit_price
        slippage_pts = round(actual_fill - ref_price, 2) if tx_type == "BUY" else round(ref_price - actual_fill, 2)
        slippage_inr = round(slippage_pts * quantity, 2)
        slippage_pct = round((slippage_pts / ref_price) * 100.0, 3) if ref_price > 0 else 0.0

        telemetry = {
            "order_id": placed_order_id,
            "status": status,
            "tradingsymbol": tradingsymbol,
            "transaction_type": tx_type,
            "quantity": quantity,
            "reference_price": round(ref_price, 2),
            "executed_price": round(actual_fill, 2) if status in ["COMPLETE", "FILLED"] else None,
            "slippage_pts": slippage_pts if status in ["COMPLETE", "FILLED"] else 0.0,
            "slippage_inr": slippage_inr if status in ["COMPLETE", "FILLED"] else 0.0,
            "slippage_pct": slippage_pct if status in ["COMPLETE", "FILLED"] else 0.0,
            "worst_acceptable_price": worst_acceptable_price,
            "chase_attempts": attempts_taken,
            "latency_ms": elapsed_ms,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

        self.execution_audit_log.append(telemetry)
        if len(self.execution_audit_log) > 500:
            self.execution_audit_log = self.execution_audit_log[-500:]

        return telemetry

    async def execute_basket_with_margin_lock(
        self,
        legs: List[Dict[str, Any]],
        broker=None,
        user_id: str = "default_user",
        basket_name: str = "Multi-Leg Spread"
    ) -> Dict[str, Any]:
        """
        Executes a multi-leg options basket honoring the Hedge-First protocol:
        1. BUY (protective) legs placed FIRST to unlock SEBI margin benefit.
        2. SELL legs placed SECOND with smart limit chasing.
        3. If any critical leg fails, halts to avoid naked exposure.
        """
        active_broker = broker or self.broker
        if not active_broker:
            raise ValueError("No active broker available for basket execution.")

        start_time = time.time()
        logger.info(f"🧺 [BasketExec] Initiating Basket '{basket_name}' with {len(legs)} legs.")

        # Sort legs: BUY legs first (hedge), then SELL legs
        sorted_legs = sorted(legs, key=lambda x: 0 if x.get("transaction_type", "BUY").upper() == "BUY" else 1)

        executed_legs = []
        failed_legs = []

        for idx, leg in enumerate(sorted_legs):
            leg_name = leg.get("tradingsymbol", f"Leg-{idx+1}")
            tx_type = leg.get("transaction_type", "BUY").upper()
            logger.info(f"➡️ [BasketExec] Step {idx+1}/{len(sorted_legs)}: Executing {tx_type} for {leg_name}")

            res = await self.execute_smart_order(
                order_request=leg,
                broker=active_broker,
                user_id=user_id
            )

            if res.get("status") in ["COMPLETE", "FILLED", "MOCK_FILLED"]:
                executed_legs.append(res)
            else:
                logger.error(f"❌ [BasketExec] Leg {leg_name} failed: {res.get('status')}")
                failed_legs.append({"leg": leg, "result": res})
                break

        is_partial_failure = len(failed_legs) > 0 and len(executed_legs) > 0
        if is_partial_failure and self.notifier:
            self.notifier.notify_sync(
                f"⚠️ *Basket Execution Alert ({basket_name})*\n"
                f"Executed: {len(executed_legs)} legs.\n"
                f"Failed at: `{failed_legs[0]['leg'].get('tradingsymbol')}`\n"
                f"Check positions immediately to manage orphan exposure."
            )

        total_elapsed = round((time.time() - start_time) * 1000, 1)
        total_slippage_inr = sum(leg.get("slippage_inr", 0.0) for leg in executed_legs)

        return {
            "basket_name": basket_name,
            "status": "COMPLETE" if len(failed_legs) == 0 else "PARTIAL_FAILURE" if len(executed_legs) > 0 else "FAILED",
            "total_legs": len(legs),
            "executed_count": len(executed_legs),
            "failed_count": len(failed_legs),
            "executed_legs": executed_legs,
            "failed_legs": failed_legs,
            "total_slippage_inr": round(total_slippage_inr, 2),
            "total_latency_ms": total_elapsed,
            "timestamp": datetime.now().isoformat()
        }

    async def _fetch_live_ltp(self, broker, exchange: str, tradingsymbol: str) -> float:
        try:
            if hasattr(broker, "ltp"):
                key = f"{exchange}:{tradingsymbol}" if ":" not in tradingsymbol else tradingsymbol
                res = broker.ltp(key)
                if isinstance(res, dict):
                    data = res.get(key) or res.get(tradingsymbol)
                    if isinstance(data, dict):
                        return float(data.get("last_price", 0.0))
            return 0.0
        except Exception as e:
            logger.debug(f"Failed to fetch live LTP for {tradingsymbol}: {e}")
            return 0.0

    async def _check_order_status(self, broker, order_id: str) -> Dict[str, Any]:
        try:
            if hasattr(broker, "orders"):
                orders = broker.orders()
                if isinstance(orders, list):
                    for o in orders:
                        if str(o.get("order_id")) == str(order_id) or str(o.get("orderid")) == str(order_id):
                            return {
                                "status": o.get("status") or o.get("orderstatus") or "OPEN",
                                "average_price": o.get("average_price") or o.get("averageprice") or 0.0,
                                "filled_quantity": o.get("filled_quantity") or o.get("filledshares") or 0,
                                "reason": o.get("text") or o.get("status_message") or ""
                            }
            return {"status": "OPEN", "average_price": 0.0}
        except Exception as e:
            logger.warning(f"Error checking order status {order_id}: {e}")
            return {"status": "OPEN", "average_price": 0.0}

    async def _modify_order_safe(self, broker, order_id: str, **kwargs):
        try:
            if hasattr(broker, "modify_order"):
                broker.modify_order(order_id=order_id, **kwargs)
            elif hasattr(broker, "smart_api") and hasattr(broker.smart_api, "modifyOrder"):
                params = {
                    "variety": "NORMAL",
                    "orderid": str(order_id),
                    "ordertype": "LIMIT",
                    "producttype": kwargs.get("product", "INTRADAY"),
                    "duration": "DAY",
                    "price": kwargs.get("price", 0),
                    "quantity": kwargs.get("quantity", 1),
                    "tradingsymbol": kwargs.get("tradingsymbol"),
                    "symboltoken": kwargs.get("symboltoken", ""),
                    "exchange": kwargs.get("exchange", "NFO")
                }
                broker.smart_api.modifyOrder(params)
        except Exception as e:
            logger.warning(f"Modify order {order_id} failed: {e}")

    async def _cancel_order_safe(self, broker, order_id: str):
        try:
            if hasattr(broker, "cancel_order"):
                broker.cancel_order(order_id)
            elif hasattr(broker, "smart_api") and hasattr(broker.smart_api, "cancelOrder"):
                broker.smart_api.cancelOrder(str(order_id), "NORMAL")
        except Exception as e:
            logger.warning(f"Cancel order {order_id} failed: {e}")

    def _is_mock_broker(self, broker) -> bool:
        if broker is None:
            return True
        class_name = broker.__class__.__name__
        return "Mock" in class_name or getattr(broker, "is_mock", False)

    async def _execute_mock_smart_fill(
        self,
        order_request: Dict[str, Any],
        ref_price: float,
        worst_acceptable_price: float,
        start_time: float,
        user_id: str
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.15)
        tx_type = order_request.get("transaction_type", "BUY").upper()
        quantity = int(order_request.get("quantity", 1))
        tradingsymbol = order_request.get("tradingsymbol", "")

        simulated_pts = round(ref_price * 0.001, 2)
        if tx_type == "BUY":
            fill_price = round(min(ref_price + simulated_pts, worst_acceptable_price), 2)
            slippage_pts = round(fill_price - ref_price, 2)
        else:
            fill_price = round(max(ref_price - simulated_pts, worst_acceptable_price), 2)
            slippage_pts = round(ref_price - fill_price, 2)

        slippage_inr = round(slippage_pts * quantity, 2)
        slippage_pct = round((slippage_pts / ref_price) * 100.0, 3) if ref_price > 0 else 0.0
        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        sim_order_id = f"SMART_SIM_{int(time.time() * 1000) % 10000000}"

        telemetry = {
            "order_id": sim_order_id,
            "status": "MOCK_FILLED",
            "tradingsymbol": tradingsymbol,
            "transaction_type": tx_type,
            "quantity": quantity,
            "reference_price": round(ref_price, 2),
            "executed_price": fill_price,
            "slippage_pts": slippage_pts,
            "slippage_inr": slippage_inr,
            "slippage_pct": slippage_pct,
            "worst_acceptable_price": worst_acceptable_price,
            "chase_attempts": 1,
            "latency_ms": elapsed_ms,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_audit_log.append(telemetry)
        return telemetry


# Global singleton instance
smart_execution_engine = SmartExecutionEngine()
