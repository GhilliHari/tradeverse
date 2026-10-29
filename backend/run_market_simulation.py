#!/usr/bin/env python3
"""
Headless Market-Hours Simulation & Offline Catch-Up Runner for Tradeverse.
Works both during live market hours (09:15 - 15:30 IST) and when triggered
after the system was off/asleep or via GitHub Actions Cloud Cron.
"""

import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MarketSimulationRunner")


async def run_single_cycle(days_back: int = 14, push_to_github: bool = False):
    from simulation_engine import SimulationEngine
    from paper_manager import paper_manager
    from github_backup_manager import github_backup_manager

    # 0. Ensure any missing backup data is restored/supported from GitHub first
    restore_res = github_backup_manager.restore_from_github()
    if restore_res.get("restored_files_count", 0) > 0:
        logger.info(f"Restored {restore_res['restored_files_count']} backup files from GitHub.")

    base_dir = Path(__file__).parent
    eng = SimulationEngine(data_dir=str(base_dir / "observatory_data"))

    # 1. Auto-close any expired paper positions
    closed_stale = paper_manager.auto_close_stale_positions(hold_minutes=15)
    if closed_stale:
        logger.info(f"Closed {closed_stale} expired paper positions.")

    # 2. Backfill any missed market hours from historical 5m market candles
    bf_res = eng.backfill_missed_market_hours(days_back=days_back)
    logger.info(f"Market-Hours Catch-Up Status: {bf_res.get('days_backfilled')} days updated, "
                f"{bf_res.get('total_trades_logged')} option trades synced.")

    # 3. If currently inside market hours (09:15 - 15:30 IST), also run live AI capture & outcome check
    if eng.is_market_hours() or len(eng.active_predictions) > 0:
        from config import config
        from agent_layer import IntelligenceLayer
        intel = IntelligenceLayer(config.GEMINI_API_KEY)

        if eng.active_predictions:
            processed = await eng.check_outcomes(intel)
            logger.info(f"Processed {processed} pending live outcomes.")

        if eng.is_market_hours():
            for sym in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]:
                pred = await eng.capture_prediction(intel, symbol=sym)
                if pred:
                    pred["symbol"] = sym
                    eng._save_prediction(pred)
                    logger.info(f"Live prediction captured for {sym}: {pred['prediction']['signal']} @ {pred['prediction']['strike']}")

    summary = eng.get_performance_summary()
    logger.info(f"Latest Session ({summary.get('date')}): "
                f"Trades={summary.get('active_trades_count', 0)}, "
                f"WinRate={summary.get('win_rate', 0)}%, "
                f"TotalPnL=₹{summary.get('total_pnl', 0):,.2f}")

    # 4. Update GitHub backup manifests (`latest_summary.json` & `backup_manifest.json`)
    github_backup_manager.generate_backup_manifests(
        sim_status=eng.get_status(),
        sim_summary=summary,
        sim_results=eng.get_results(),
        paper_summary=paper_manager.get_summary(),
    )

    if push_to_github:
        bk_res = github_backup_manager.backup_to_github()
        logger.info(f"GitHub Backup Sync: status={bk_res.get('status')}, commit={bk_res.get('commit_hash')}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tradeverse Market-Hours Simulation Runner")
    parser.add_argument("--days", type=int, default=14, help="Days to check for offline market-hours catch-up")
    parser.add_argument("--push", action="store_true", help="Commit and push updated backup data to GitHub")
    args = parser.parse_args()
    asyncio.run(run_single_cycle(days_back=args.days, push_to_github=args.push))

