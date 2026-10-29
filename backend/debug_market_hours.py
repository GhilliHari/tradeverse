
from simulation_engine import SimulationEngine
from datetime import datetime

se = SimulationEngine()
now = datetime.now()
is_hours = se.is_market_hours()

print(f"Current Date/Time: {now}")
print(f"Weekday: {now.weekday()}")
print(f"Market Hours?: {is_hours}")

# Debug specific components
holidays = [
    '2026-03-03', '2026-03-17'
]
print(f"Is today ({now.strftime('%Y-%m-%d')}) in holidays? {now.strftime('%Y-%m-%d') in holidays}")
print(f"Is 9:15 <= {now.time()} <= 15:30? {se.market_open <= now.time() <= se.market_close}")
