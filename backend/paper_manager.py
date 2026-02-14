import json
import os
import time
from datetime import datetime
import logging

logger = logging.getLogger("PaperManager")

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

    def place_trade(self, symbol, side, quantity, price, type="MARKET", reasoning="", mode="MANUAL"):
        """
        Logs a new trade entry (OPEN).
        """
        trade_id = f"PAPER_{int(time.time() * 1000)}"
        entry = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": "OPEN",
            "symbol": symbol,
            "side": side,  # BUY/SELL
            "quantity": quantity,
            "entry_price": price,
            "type": type,
            "status": "OPEN",
            "pnl": 0.0,
            "reasoning": reasoning,
            "mode": mode  # MANUAL, AUTO, SIMULATION
        }
        if self._append_log(entry):
            return entry
        return None

    def close_trade(self, trade_id, exit_price, reasoning=""):
        """
        Logs a trade exit and calculates PnL. 
        Note: This appends a NEW log entry with action="CLOSE" linked to the trade_id.
        It does NOT modify the original OPEN entry, preserving history.
        """
        # First, find the opening trade to calculate PnL
        open_trade = self.get_trade(trade_id)
        if not open_trade:
            logger.error(f"Trade ID {trade_id} not found.")
            return None

        qty = open_trade.get("quantity", 0)
        entry_price = open_trade.get("entry_price", 0)
        side = open_trade.get("side", "BUY")

        if side == "BUY":
            pnl = (exit_price - entry_price) * qty
        else:
            pnl = (entry_price - exit_price) * qty

        entry = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": "CLOSE",
            "symbol": open_trade.get("symbol"),
            "side": side,
            "quantity": qty,
            "entry_price": entry_price,
            "exit_price": exit_price,
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

# Global Instance
paper_manager = PaperManager()
