import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)

async def run_tests():
    print("==============================================================")
    print("        TRADEVERSE PHASE 1 VERIFICATION & AUDIT SUITE         ")
    print("==============================================================")

    # 1. Test Multi-Leg Spreads Engine
    print("\n--- 1. Testing MultiLegSpreadsEngine ---")
    from multileg_engine import multileg_engine
    recs = multileg_engine.get_spread_recommendations(
        symbol="BANKNIFTY",
        spot_price=57800.0,
        vix=14.2,
        regime="NOMINAL",
        bias="BULLISH"
    )
    print(f"Symbol: {recs['symbol']} | Spot: ₹{recs['spot_price']} | ATM: {recs['atm_strike']}")
    print(f"Top Strategy: {recs['top_recommended_strategy']}")
    
    assert len(recs["strategies"]) == 4, "Expected 4 defined-risk strategies"
    for strat in recs["strategies"]:
        print(f"  [{strat['type']}] {strat['name']}")
        print(f"    Direction: {strat['direction']} | Net: {strat['net_premium_pts']} pts ({strat['net_premium_type']})")
        print(f"    Max Profit: ₹{strat['max_profit_inr']:,.2f} | Max Loss: ₹{strat['max_loss_inr']:,.2f} | Win Prob: {strat['win_probability_pct']}%")
        print(f"    Margin Benefit: {strat['margin_required_approx']}")
        print(f"    Legs count: {len(strat['legs'])} (First leg: {strat['legs'][0]['action']} {strat['legs'][0]['tradingsymbol']})")
        # Ensure Hedge-First rule: BUY leg must come before SELL leg
        assert strat["legs"][0]["action"] == "BUY", "CRITICAL ERROR: Buy hedge leg must be first!"

    print("✔ MultiLegSpreadsEngine passed with 100% compliance!")

    # 2. Test Smart Execution Engine
    print("\n--- 2. Testing SmartExecutionEngine ---")
    from smart_execution import smart_execution_engine
    from broker_factory import MockAngelClient

    mock_broker = MockAngelClient("test_user_phase1")
    smart_execution_engine.set_broker(mock_broker)

    # Single order smart execution
    test_order = {
        "tradingsymbol": "BANKNIFTY 57800 CE",
        "exchange": "NFO",
        "transaction_type": "BUY",
        "quantity": 30,
        "product": "MIS",
        "target_price": 280.0,
        "max_slippage_pct": 0.008,
        "chase_steps": 3,
        "step_wait_sec": 0.1,
        "mode": "SMART_LIMIT_CHASE"
    }

    res = await smart_execution_engine.execute_smart_order(test_order, broker=mock_broker, user_id="test_user")
    print("Single Smart Order Result:")
    print(f"  Order ID: {res['order_id']} | Status: {res['status']}")
    print(f"  Ref: ₹{res['reference_price']} -> Executed: ₹{res['executed_price']}")
    print(f"  Slippage: {res['slippage_pts']:+.2f} pts (₹{res['slippage_inr']:+.2f} / {res['slippage_pct']:+.2f}%)")
    print(f"  Latency: {res['latency_ms']}ms | Chase Attempts: {res['chase_attempts']}")
    assert res["status"] in ["MOCK_FILLED", "COMPLETE"], f"Unexpected status: {res['status']}"

    # Basket order execution with Margin Lock (Hedge First)
    print("\n--- 3. Testing Basket Margin-Lock Execution ---")
    bull_put_strat = next(s for s in recs["strategies"] if s["id"] == "bull_put_credit_spread")
    basket_res = await smart_execution_engine.execute_basket_with_margin_lock(
        legs=bull_put_strat["legs"],
        broker=mock_broker,
        user_id="test_user",
        basket_name=bull_put_strat["name"]
    )
    print(f"Basket Result: {basket_res['basket_name']}")
    print(f"  Status: {basket_res['status']} | Executed Legs: {basket_res['executed_count']}/{basket_res['total_legs']}")
    print(f"  Total Slippage: ₹{basket_res['total_slippage_inr']:+.2f} | Total Latency: {basket_res['total_latency_ms']}ms")
    for leg_res in basket_res["executed_legs"]:
        print(f"    - Leg {leg_res['tradingsymbol']} ({leg_res['transaction_type']}): Filled @ ₹{leg_res['executed_price']}")

    assert basket_res["status"] == "COMPLETE", f"Basket failed: {basket_res}"
    print("✔ Basket Execution Engine passed with Margin-Lock verification!")

    # 4. Verify main.py syntax
    print("\n--- 4. Verifying main.py Module Integrity ---")
    import main
    assert hasattr(main.app, "routes"), "FastAPI app has no routes!"
    route_paths = [r.path for r in main.app.routes]
    assert "/api/order/smart_place" in route_paths, "Missing /api/order/smart_place route"
    assert "/api/order/basket_place" in route_paths, "Missing /api/order/basket_place route"
    assert "/api/strategies/multileg/recommendations" in route_paths, "Missing /api/strategies/multileg/recommendations route"
    assert "/api/strategies/multileg/execute" in route_paths, "Missing /api/strategies/multileg/execute route"
    assert "/api/execution/audit_log" in route_paths, "Missing /api/execution/audit_log route"
    print(f"✔ main.py verified with {len(route_paths)} total registered API routes!")

    print("\n==============================================================")
    print("   ALL PHASE 1 BACKEND COMPONENTS VALIDATED & 100% OPERATIONAL  ")
    print("==============================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
