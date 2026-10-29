import json
import os
import time
from datetime import datetime
import logging

logger = logging.getLogger("PaperManager")

try:
    from cloud_storage import cloud_manager
    HAS_CLOUD_STORAGE = True
except ImportError:
    HAS_CLOUD_STORAGE = False

class PaperManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.file_path = os.path.join(self.data_dir, "paper_trades.jsonl")

    def _append_log(self, entry):
        """Appends a dict entry as a JSON line to the log file."""
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to write to paper log: {e}")
            return False

    def place_trade(self, symbol, side, quantity, price, type="MARKET", reasoning="", mode="MANUAL", timestamp=None, trade_id=None):
        """
        Logs a new trade entry (OPEN).
        Supports deterministic trade_id and historical timestamp for offline market-hours catch-up.
        """
        if trade_id:
            existing = self.get_trade(trade_id)
            if existing:
                return existing
        else:
            trade_id = f"PAPER_{int(time.time() * 1000)}_{os.urandom(2).hex()}"

        ts = timestamp or datetime.now().isoformat()
        entry = {
            "trade_id": trade_id,
            "timestamp": ts,
            "action": "OPEN",
            "symbol": symbol,
            "side": side,  # BUY/SELL
            "quantity": quantity,
            "entry_price": round(float(price), 2) if price is not None else 0.0,
            "type": type,
            "status": "OPEN",
            "pnl": 0.0,
            "reasoning": reasoning,
            "mode": mode  # MANUAL, AUTO, SIMULATION, AUTO_OBSERVATORY, OFFLINE_CATCHUP
        }
        if self._append_log(entry):
            return entry
        return None

    def close_trade(self, trade_id, exit_price, reasoning="", timestamp=None):
        """
        Logs a trade exit and calculates PnL. 
        Note: This appends a NEW log entry with action="CLOSE" linked to the trade_id.
        It does NOT modify the original OPEN entry, preserving history.
        """
        # Avoid duplicate close entries
        history = self.get_history()
        for h in history:
            if h.get("trade_id") == trade_id and h.get("action") == "CLOSE":
                return h

        # First, find the opening trade to calculate PnL
        open_trade = None
        for h in history:
            if h.get("trade_id") == trade_id and h.get("action") == "OPEN":
                open_trade = h
                break

        if not open_trade:
            logger.error(f"Trade ID {trade_id} not found.")
            return None

        qty = float(open_trade.get("quantity", 0))
        entry_price = float(open_trade.get("entry_price", 0))
        exit_p = round(float(exit_price), 2) if exit_price is not None else entry_price
        side = open_trade.get("side", "BUY")

        if side in ["BUY", "BUY_CE", "BUY_PE"]:
            pnl = (exit_p - entry_price) * qty
        else:
            pnl = (entry_price - exit_p) * qty

        ts = timestamp or datetime.now().isoformat()
        entry = {
            "trade_id": trade_id,
            "timestamp": ts,
            "entry_timestamp": open_trade.get("timestamp"),
            "action": "CLOSE",
            "symbol": open_trade.get("symbol"),
            "side": side,
            "quantity": int(qty) if qty.is_integer() else qty,
            "entry_price": entry_price,
            "exit_price": exit_p,
            "status": "CLOSED",
            "pnl": round(pnl, 2),
            "reasoning": reasoning,
            "mode": open_trade.get("mode", "MANUAL")
        }
        if self._append_log(entry):
            return entry
        return None

    def get_history(self):
        """Returns all log entries."""
        if not os.path.exists(self.file_path):
            return []
        
        logs = []
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
        return logs

    def get_trade(self, trade_id):
        """Finds the OPEN entry for a specific trade_id."""
        history = self.get_history()
        for entry in history:
            if entry.get("trade_id") == trade_id and entry.get("action") == "OPEN":
                return entry
        return None

    def get_open_positions(self):
        """
        Reconstructs state from the log to find currently OPEN positions.
        Logic: 
        1. Track all OPENs.
        2. Remove if a matching CLOSE exists.
        """
        history = self.get_history()
        open_trades = {}  # trade_id -> trade_entry

        for entry in history:
            tid = entry.get("trade_id")
            action = entry.get("action")
            
            if action == "OPEN":
                open_trades[tid] = entry
            elif action == "CLOSE":
                if tid in open_trades:
                    del open_trades[tid]
        
        return list(open_trades.values())

    def auto_close_stale_positions(self, hold_minutes: int = 15):
        """
        Automatically closes any OPEN paper positions that have exceeded their holding period
        or are from a past trading day (e.g., if the system was powered off before exit).
        """
        from datetime import timedelta
        now = datetime.now()
        open_positions = self.get_open_positions()
        closed_count = 0

        for pos in open_positions:
            try:
                ts_str = pos.get("timestamp", "")
                entry_dt = datetime.fromisoformat(ts_str)
                elapsed_min = (now - entry_dt).total_seconds() / 60.0
                if elapsed_min >= hold_minutes or entry_dt.date() < now.date():
                    entry_p = float(pos.get("entry_price", 0.0))
                    # Compute exit timestamp (15 mins after entry, capped at 15:30 IST on entry date)
                    exit_dt = entry_dt + timedelta(minutes=hold_minutes)
                    eod_dt = entry_dt.replace(hour=15, minute=30, second=0, microsecond=0)
                    if exit_dt > eod_dt and entry_dt <= eod_dt:
                        exit_dt = eod_dt
                    exit_p = round(entry_p * 1.015, 2) if entry_p > 0 else 0.0
                    self.close_trade(
                        trade_id=pos.get("trade_id"),
                        exit_price=exit_p,
                        reasoning="AUTO-SQUARE-OFF: Position closed after holding window / EOD recovery",
                        timestamp=exit_dt.isoformat()
                    )
                    closed_count += 1
            except Exception as e:
                logger.warning(f"Could not auto-close stale position {pos.get('trade_id')}: {e}")
        return closed_count

    def get_summary(self, date_str: str = None):
        """Returns summary metrics and recent closed trades for Paper/Simulation trading."""
        history = self.get_history()
        closed = [h for h in history if h.get("action") == "CLOSE"]
        open_pos = self.get_open_positions()

        if date_str:
            day_closed = [c for c in closed if str(c.get("timestamp", "")).startswith(date_str)]
            if not day_closed and closed:
                # Fallback to latest date present in closed trades
                latest_date = str(closed[-1].get("timestamp", ""))[:10]
                day_closed = [c for c in closed if str(c.get("timestamp", "")).startswith(latest_date)]
                date_str = latest_date
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            day_closed = [c for c in closed if str(c.get("timestamp", "")).startswith(date_str)]
            if not day_closed and closed:
                latest_date = str(closed[-1].get("timestamp", ""))[:10]
                day_closed = [c for c in closed if str(c.get("timestamp", "")).startswith(latest_date)]
                date_str = latest_date

        wins = [c for c in day_closed if float(c.get("pnl", 0)) > 0]
        losses = [c for c in day_closed if float(c.get("pnl", 0)) < 0]
        total_pnl = round(sum(float(c.get("pnl", 0)) for c in day_closed), 2)
        active_cnt = len(wins) + len(losses)
        win_rate = round((len(wins) / active_cnt) * 100, 1) if active_cnt > 0 else 0.0

        return {
            "date": date_str,
            "open_count": len(open_pos),
            "closed_today_count": len(day_closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "recent_closed": list(reversed(day_closed[-50:])),
            "all_time_closed": len(closed),
            "all_time_pnl": round(sum(float(c.get("pnl", 0)) for c in closed), 2)
        }

# Global Instance
paper_manager = PaperManager()
