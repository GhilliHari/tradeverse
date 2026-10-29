
import json
import os
from datetime import datetime, timedelta

data_dir = "/Users/teju/.gemini/antigravity/scratch/tradeverse/backend/observatory_data"
date_str = datetime.now().strftime("%Y-%m-%d")
file_path = os.path.join(data_dir, f"simulation_{date_str}.json")

if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
else:
    data = {"date": date_str, "predictions": []}

# Add a Completed Profitable Prediction
completed_pred = {
    "timestamp": (datetime.now() - timedelta(minutes=45)).isoformat(),
    "prediction": {
        "signal": "BUY_CE",
        "strike": 60800,
        "confidence": 0.85,
        "entry_price": 245.50,
        "model_scores": {"technical": 0.8, "sentiment": 0.9},
        "regime": "NOMINAL"
    },
    "market_context": {
        "spot_price": 60750.0,
        "vix": 14.2,
        "regime": "NOMINAL"
    },
    "actual_outcome": {
        "exit_timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "exit_price": 312.40,
        "pnl": 1003.50, # (312.4 - 245.5) * 15
        "pnl_pct": 27.2,
        "max_favorable": 325.0,
        "max_adverse": 240.0,
        "holding_period_minutes": 30
    },
    "status": "COMPLETED"
}

# Add a Pending Prediction
pending_pred = {
    "timestamp": datetime.now().isoformat(),
    "prediction": {
        "signal": "BUY_PE",
        "strike": 60600,
        "confidence": 0.72,
        "entry_price": 198.20,
        "model_scores": {"technical": -0.7, "sentiment": -0.8},
        "regime": "VOLATILE"
    },
    "market_context": {
        "spot_price": 60669.0,
        "vix": 15.5,
        "regime": "VOLATILE"
    },
    "actual_outcome": None,
    "status": "PENDING"
}

data['predictions'].append(completed_pred)
data['predictions'].append(pending_pred)

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Populated Observatory with 1 COMPLETED and 1 PENDING non-HOLD order for {date_str}")
