import math
import logging
from datetime import datetime, time, date
from typing import Dict, Tuple

logger = logging.getLogger("AstroEngine")

class AstroEngine:
    """
    Pillar 3: Financial Astrology & Gann Time Cycle Engine for Tradeverse.
    Calculates lunar phase cycles, Gann intraday turning windows, and planetary energy alignment.
    """

    def __init__(self):
        # Key Gann Intraday Turning Windows (IST) for BankNifty / Nifty
        self.gann_windows = [
            (time(9, 45), time(10, 0), "INITIAL_BALANCE_PIVOT", "High probability 1st pivot turn zone"),
            (time(11, 15), time(11, 30), "MID_SESSION_TRANSITION", "Morning trend exhaustion / consolidation zone"),
            (time(13, 15), time(13, 30), "EUROPEAN_OPEN_REACTION", "Global liquidity inflow / volatility surge window"),
            (time(14, 15), time(14, 30), "POWER_HOUR_ACCELERATION", "Final trend continuation or sharp short-squeeze window")
        ]
        logger.info("🔮 AstroEngine Initialized (Lunar Cycles & Gann Time Turns)")

    def calculate_lunar_phase(self, dt: datetime = None) -> Dict:
        """
        Calculates Lunar Phase angle (0° to 360°) and status.
        New Moon (0°) & Full Moon (180°) are major institutional reversal dates.
        """
        if dt is None:
            dt = datetime.now()

        # Known New Moon reference point: Jan 11, 2024 11:57 UTC
        ref_date = datetime(2024, 1, 11, 11, 57)
        synodic_month = 29.53058867 # days per lunar cycle

        delta_days = (dt - ref_date).total_seconds() / 86400.0
        cycle_progress = (delta_days % synodic_month) / synodic_month
        phase_deg = cycle_progress * 360.0

        phase_name = "NEUTRAL"
        reversal_probability = "NORMAL"
        directional_bias = 0.0

        if phase_deg <= 12 or phase_deg >= 348:
            phase_name = "NEW_MOON (Amavasya)"
            reversal_probability = "EXTREME_HIGH"
            directional_bias = 0.5 # Bullish expansion setup
        elif 168 <= phase_deg <= 192:
            phase_name = "FULL_MOON (Purnima)"
            reversal_probability = "EXTREME_HIGH"
            directional_bias = -0.5 # Reversal / Profit Taking setup
        elif 80 <= phase_deg <= 100:
            phase_name = "FIRST_QUARTER"
            reversal_probability = "MODERATE"
            directional_bias = 0.2
        elif 260 <= phase_deg <= 280:
            phase_name = "THIRD_QUARTER"
            reversal_probability = "MODERATE"
            directional_bias = -0.2

        illumination_pct = round(0.5 * (1 - math.cos(math.radians(phase_deg))) * 100.0, 1)

        return {
            "phase_deg": round(phase_deg, 1),
            "phase_name": phase_name,
            "illumination_pct": illumination_pct,
            "reversal_probability": reversal_probability,
            "directional_bias": directional_bias
        }

    def check_gann_time_window(self, dt: datetime = None) -> Dict:
        """
        Checks if the current time falls into a Gann Intraday Turning Window.
        """
        if dt is None:
            dt = datetime.now()

        current_t = dt.time()
        
        for start_t, end_t, window_name, description in self.gann_windows:
            if start_t <= current_t <= end_t:
                return {
                    "is_gann_window": True,
                    "window_name": window_name,
                    "description": description,
                    "intensity": "HIGH"
                }

        return {
            "is_gann_window": False,
            "window_name": "NONE",
            "description": "Standard market hours",
            "intensity": "NORMAL"
        }

    def get_astro_analysis(self, dt: datetime = None) -> Dict:
        """
        Calculates the aggregate Financial Astrology & Gann Time score (-1.0 to +1.0).
        """
        if dt is None:
            dt = datetime.now()

        lunar = self.calculate_lunar_phase(dt)
        gann = self.check_gann_time_window(dt)

        astro_score = lunar['directional_bias']

        # If we are inside a Gann Turning Window, amplify conviction score
        if gann['is_gann_window']:
            astro_score *= 1.35
            logger.info(f"✨ Gann Time Window Active: {gann['window_name']} | Astro Score: {astro_score:.2f}")

        astro_score = max(-1.0, min(1.0, astro_score))

        return {
            "astro_score": round(astro_score, 2),
            "lunar_phase": lunar,
            "gann_window": gann,
            "summary": f"{lunar['phase_name']} | Gann Status: {gann['window_name']}"
        }
