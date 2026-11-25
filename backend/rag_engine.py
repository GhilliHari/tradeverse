"""
Tradeverse RAG (Retrieval-Augmented Generation) Engine.
Embedded, zero-cost, persistent vector store using ChromaDB and ONNX embeddings.

Collections:
1. 'trading_playbook': Systematic quant trading strategies, GEX rules, CPR, VWAP, Gann.
2. 'historical_regimes': Case studies of past market regimes (Budget, RBI MPC, Gamma Squeezes).
3. 'banking_research': Structural fundamentals & drivers for Bank Nifty heavyweight banks.
4. 'trader_journal': Personal trading rules, risk boundaries, and mistake post-mortems.
"""

import os
import logging
from typing import List, Dict, Optional, Any
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

logger = logging.getLogger("tradeverse.rag")

# Path for persistent vector storage
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
CHROMA_PERSIST_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "chroma_db")

os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Default collections
COLLECTIONS = [
    "trading_playbook",
    "historical_regimes",
    "banking_research",
    "trader_journal"
]

# --- Curated Seed Data for Initial Knowledge Base ---

SEED_PLAYBOOK = [
    {
        "id": "playbook_cpr_breakout",
        "document": (
            "CPR (Central Pivot Range) Breakout Strategy for Bank Nifty:\n"
            "1. Narrow CPR indicates an impending high-momentum trending day (>500 point move expected).\n"
            "2. Wide CPR indicates a range-bound, sideways mean-reverting market; avoid buying breakouts and focus on range fade strategies.\n"
            "3. Virgin CPR (untested in previous session) acts as a high-probability magnetic support/resistance target.\n"
            "4. Bullish Trigger: 5-minute candle closing decisively above Top Central (TC) with rising volume. Target R1/R2, SL below Pivot (P)."
        ),
        "metadata": {"category": "technical", "topic": "cpr", "timeframe": "intraday", "asset": "BANKNIFTY"}
    },
    {
        "id": "playbook_gex_walls",
        "document": (
            "Gamma Exposure (GEX) & Option Wall Pinning Rules:\n"
            "1. Upper Gamma Wall (Call Wall) is the strike with the largest open interest and positive gamma. Dealers act as net sellers as price rises, creating a strong ceiling.\n"
            "2. Lower Gamma Wall (Put Wall) has the largest Put OI. Dealers act as net buyers on dips, providing a strong institutional floor.\n"
            "3. No-Trade Chop Zone: The range between Lower and Upper Gamma Walls where volatility is dampening and price tends to chop/mean-revert.\n"
            "4. Gamma Squeeze / Breakout: If Bank Nifty breaches the Call Wall with rapid Call unwinding (negative OI change), dealers are forced to buy futures, triggering violent upward expansion."
        ),
        "metadata": {"category": "derivatives", "topic": "gex", "strategy": "options", "asset": "BANKNIFTY"}
    },
    {
        "id": "playbook_vwap_orderflow",
        "document": (
            "VWAP & Institutional Order Flow Delta Execution:\n"
            "1. Volume Weighted Average Price (VWAP) represents institutional fair value benchmark for intraday players.\n"
            "2. Cumulative Volume Delta (CVD) Divergence: If price makes a new high but CVD makes a lower high, smart money is absorbing buyers (absorption/exhaustion); prepare for mean reversion to VWAP.\n"
            "3. Retest Entry: Never chase extended price >1.5% away from VWAP. Wait for a pullback to the VWAP + 20 EMA confluence band with supportive volume before entering."
        ),
        "metadata": {"category": "orderflow", "topic": "vwap", "indicator": "cvd", "asset": "ALL"}
    },
    {
        "id": "playbook_0dte_expiry",
        "document": (
            "0DTE & Weekly Expiry Trading Discipline:\n"
            "1. Theta Decay Acceleration: Option premium decay accelerates exponentially after 1:30 PM on expiry day.\n"
            "2. Gamma Sniper: OTM options (1 strike away from ATM) experience asymmetric delta expansion if price breaches key levels between 2:00 PM and 3:15 PM.\n"
            "3. Capital Allocation: Allocate no more than 15% of intraday trading margin to expiry hero-or-zero contracts. Strictly risk-define every position with stop losses."
        ),
        "metadata": {"category": "derivatives", "topic": "expiry", "strategy": "0dte", "asset": "BANKNIFTY"}
    },
    {
        "id": "playbook_gann_harmonics",
        "document": (
            "Gann Mathematical Angle & Price-Time Harmonic Rules:\n"
            "1. Square of 9 Expansion: 90-degree and 180-degree price intervals from major swing pivots act as natural mathematical resistance and support turning points.\n"
            "2. Time Cycle Confluence: Major trend reversals frequently align with planetary aspect confluences (Trines 120°, Squares 90°, Conjunctions) matching historical cyclical turns.\n"
            "3. Confirmation: Use Gann harmonic levels strictly in conjunction with options open interest walls and price action confirmation."
        ),
        "metadata": {"category": "gann", "topic": "harmonics", "asset": "BANKNIFTY"}
    }
]

SEED_REGIMES = [
    {
        "id": "regime_union_budget",
        "document": (
            "Historical Regime — Union Budget Volatility Pattern:\n"
            "1. Pre-Budget IV Surge: India VIX typically rallies 20-40% leading into Budget announcement day, causing severe option premium inflation.\n"
            "2. Post-Speech IV Crush: Immediately following the Finance Minister's speech (usually around 12:30 PM - 1:00 PM), implied volatility crashes rapidly by 30-50%.\n"
            "3. Trading Strategy: Buying naked options after 12:00 PM on Budget Day suffers massive Vega crush even if direction is correct. Defined-risk credit spreads or post-speech breakout continuation setups offer optimal risk-reward."
        ),
        "metadata": {"regime": "event_driven", "event": "union_budget", "impact": "high_iv_crush"}
    },
    {
        "id": "regime_rbi_mpc",
        "document": (
            "Historical Regime — RBI Monetary Policy (MPC) Rate Decision:\n"
            "1. Time Window: RBI policy announcement occurs at 10:00 AM, followed by the Governor's press conference at 12:00 PM.\n"
            "2. Bank Nifty Response: A status quo (rate pause) with accommodative or neutral stance typically triggers a relief rally in HDFC Bank and ICICI Bank.\n"
            "3. Surprise Reaction: Any hawkish language on inflation or Cash Reserve Ratio (CRR) increase causes immediate downside spikes in PSU and private banking heavyweights."
        ),
        "metadata": {"regime": "monetary_policy", "event": "rbi_mpc", "impact": "banking_directional"}
    },
    {
        "id": "regime_gamma_short_squeeze",
        "document": (
            "Historical Regime — Expiry Day Gamma Short Squeeze:\n"
            "1. Mechanism: Occurs when Call writers with heavy OI at the nearest round strike (e.g., 52,000 CE) are trapped by an unexpected morning rally.\n"
            "2. Trigger: Price crosses the Call strike and sustains for 15 minutes; writers are forced to buy back short calls and hedge via futures.\n"
            "3. Behavior: Generates a vertical 400-800 point expansion in Bank Nifty in under 45 minutes with almost zero pullbacks until the next major round strike."
        ),
        "metadata": {"regime": "derivatives_squeeze", "event": "gamma_squeeze", "impact": "vertical_expansion"}
    },
    {
        "id": "regime_high_vix_panic",
        "document": (
            "Historical Regime — High VIX Panic / Risk-Off Regime (VIX > 22):\n"
            "1. Characteristics: Average True Range (ATR) doubles, daily candles expand to 1,500+ points, and intraday slippage increases significantly.\n"
            "2. Strategy Adjustment: Position size must be reduced by 50% immediately. Stop losses must be widened in point terms but maintained at identical monetary rupee risk.\n"
            "3. Reversals: Sharp intraday V-bottom recoveries occur frequently near multi-month volume point of control (VPOC) support zones."
        ),
        "metadata": {"regime": "high_volatility", "indicator": "vix", "impact": "wider_swings"}
    }
]

SEED_BANKING = [
    {
        "id": "bank_hdfc_fundamentals",
        "document": (
            "HDFC Bank (Weight: ~29% of Bank Nifty):\n"
            "1. The single most critical driver of Bank Nifty direction; index cannot sustain bullish trends without HDFC Bank participation.\n"
            "2. Key Fundamental Metrics: Net Interest Margin (NIM) stabilization post-merger, Credit-to-Deposit (C/D) ratio reduction towards 85%, and CASA deposit growth.\n"
            "3. Correlation: >0.85 positive intraday price correlation with Bank Nifty index."
        ),
        "metadata": {"symbol": "HDFCBANK.NS", "weight": 0.29, "sector": "private_bank"}
    },
    {
        "id": "bank_icici_fundamentals",
        "document": (
            "ICICI Bank (Weight: ~23% of Bank Nifty):\n"
            "1. High asset quality leader in the Indian banking system with Return on Assets (RoA) consistently above 2.2%.\n"
            "2. Digital Ecosystem: Strong market share in retail unsecured and SME lending with superior underwriting discipline.\n"
            "3. Market Role: Acts as the primary momentum leader during banking sector bull runs."
        ),
        "metadata": {"symbol": "ICICIBANK.NS", "weight": 0.23, "sector": "private_bank"}
    },
    {
        "id": "bank_sbi_fundamentals",
        "document": (
            "State Bank of India / SBI (Weight: ~10% of Bank Nifty):\n"
            "1. The bellwether PSU bank; primary proxy for India's macroeconomic credit demand and government capital expenditure.\n"
            "2. Sensitivity: Highly sensitive to 10-year Indian Government Bond yields, liquidity operations, and corporate credit cycle.\n"
            "3. Low Slippage & High Liquidity: Large institutional order flow absorption capacity."
        ),
        "metadata": {"symbol": "SBIN.NS", "weight": 0.10, "sector": "psu_bank"}
    },
    {
        "id": "bank_kotak_fundamentals",
        "document": (
            "Kotak Mahindra Bank (Weight: ~10% of Bank Nifty):\n"
            "1. Premium valuation bank with industry-leading capital adequacy ratio and conservative risk management.\n"
            "2. Key Catalysts: Regulatory clearances, leadership transition milestones, and net interest income trajectory."
        ),
        "metadata": {"symbol": "KOTAKBANK.NS", "weight": 0.10, "sector": "private_bank"}
    }
]

SEED_JOURNAL = [
    {
        "id": "journal_rule_theta_friday",
        "document": (
            "Trader Rule #1 — Weekend Theta Penalty:\n"
            "Never carry naked Out-of-the-Money (OTM) options over the weekend on Friday afternoons. Option decay over Saturday and Sunday guarantees 20-35% premium erosion by Monday market open even if the underlying index opens flat."
        ),
        "metadata": {"author": "trader", "rule_type": "risk_management", "priority": "high"}
    },
    {
        "id": "journal_rule_chop_discipline",
        "document": (
            "Trader Rule #2 — No-Trade Chop Zone Respect:\n"
            "If Bank Nifty is oscillating inside the No-Trade Chop Zone between the Lower Put Wall and Upper Call Wall with low volume, DO NOT take breakout trades. 80% of breakouts from the middle of the chop zone result in false bull/bear traps. Wait for a touch of the extreme walls."
        ),
        "metadata": {"author": "trader", "rule_type": "execution_discipline", "priority": "critical"}
    },
    {
        "id": "journal_rule_hard_sl",
        "document": (
            "Trader Rule #3 — Absolute Stop-Loss Integrity:\n"
            "A predefined stop-loss must be entered immediately upon trade execution. Never widen or remove a stop-loss during an active trade. If the trade thesis is invalidated, take the loss instantly and preserve capital for high-conviction setups."
        ),
        "metadata": {"author": "trader", "rule_type": "risk_management", "priority": "critical"}
    },
    {
        "id": "journal_rule_position_sizing",
        "document": (
            "Trader Rule #4 — 1% Capital Risk Limit:\n"
            "Never risk more than 1% of total account capital on any single intraday trade setup. If the distance between entry and technical stop-loss is 150 points in Bank Nifty, calculate position lot sizing strictly such that the maximum loss equals <= 1%."
        ),
        "metadata": {"author": "trader", "rule_type": "position_sizing", "priority": "high"}
    },
    {
        "id": "journal_rule_post_mortem_20261116_confidence",
        "document": (
            "Trader Rule #5 (16-Nov-2026 Lesson) — Minimum Conviction Gate:\n"
            "Never fire a live options order when AI Confidence is below 68.0% (and strictly below 72.0% during the opening hour 09:15-10:00 AM). Low confidence trades (like 30.7% PE entries) suffer high shakeout probability in normal market noise."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "entry_gate", "priority": "critical", "date": "2026-11-16"}
    },
    {
        "id": "journal_rule_post_mortem_20261116_anti_flip",
        "document": (
            "Trader Rule #6 (16-Nov-2026 Lesson) — Mandatory Cool-Off & Anti-Direction Flip:\n"
            "Enforce a strict 10-minute cool-off after any trade exit. If a trade exits at breakeven or loss, DO NOT flip to the opposite side (e.g., PE ➔ CE) for at least 20 minutes. Rapid direction flipping in the opening hour guarantees double-whipsaw losses."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "execution_discipline", "priority": "critical", "date": "2026-11-16"}
    },
    {
        "id": "journal_rule_post_mortem_20261116_tech_veto",
        "document": (
            "Trader Rule #7 (16-Nov-2026 Lesson) — Technical Trend Veto (Price Action is King):\n"
            "Technical price action must strictly agree with option direction. If 5m/15m technical score is bearish (< 0.0), Call buying is strictly VETOED regardless of bullish Macro or Sentiment scores. Never fight technical breakdown with macro hope."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "trend_confluence", "priority": "critical", "date": "2026-11-16"}
    },
    {
        "id": "journal_rule_post_mortem_20261116_5s_monitor",
        "document": (
            "Trader Rule #8 (16-Nov-2026 Lesson) — High-Frequency 5-Second Position Pulse:\n"
            "When an open real-money option contract is active, position monitoring must accelerate from 60-second scanning down to a 5-second tick loop. Slow 60s polling creates catastrophic slippage on trailing stop execution during swift candle reversals."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "risk_management", "priority": "high", "date": "2026-11-16"}
    },
    {
        "id": "journal_rule_post_mortem_20261118_runner_exemption",
        "document": (
            "Trader Rule #9 (18-Nov-2026 Lesson) — Runner Exemption on Time Exits:\n"
            "Never prematurely terminate a profitable, trending option trade on a fixed clock timer (e.g. 30-40 min). Once a trade is locked at breakeven (+0.8% net), bypass time-exits and let the dynamic trailing stop manage the position to capture massive +30% to +50% gamma breakout runs."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "exit_discipline", "priority": "critical", "date": "2026-11-18"}
    },
    {
        "id": "journal_rule_post_mortem_20261118_dynamic_trailing",
        "document": (
            "Trader Rule #10 (18-Nov-2026 Lesson) — 3-Stage Dynamic Trailing Stop:\n"
            "Rachet trailing stop-loss progressively: +3.0% profit triggers Breakeven Lock (+0.8% net), +5.0% triggers Stage 1 (trail 2.0% gap), +10.0% triggers Stage 2 Super-Runner (trail 3.0% gap), and +20.0% triggers Stage 3 Mega-Gamma (trail 4.0% gap up to +50.0%). Eliminates premature profit capping."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "risk_management", "priority": "critical", "date": "2026-11-18"}
    },
    {
        "id": "journal_rule_post_mortem_20261118_conviction_upgrade",
        "document": (
            "Trader Rule #11 (18-Nov-2026 Lesson) — High-Conviction Regime Auto-Upgrade:\n"
            "When technical momentum score is strong (|tech| >= 0.8) or AI confidence is >= 72.0%, position profile must auto-upgrade to 'TRENDING_EXPANSION'. Never box a strong trend trade into low-target nominal scalping parameters."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "regime_classification", "priority": "high", "date": "2026-11-18"}
    },
    {
        "id": "journal_rule_post_mortem_20261119_model_tier_alignment",
        "document": (
            "Trader Rule #12 (19-Nov-2026 Lesson) — Foundation AI Model Selection Protocol:\n"
            "Always bifurcate AI model roles strictly by latency vs compute density:\n"
            "1. Real-Time Intraday Trading (09:15-15:30 IST): Must use Gemini 3.8 Flash (or 3.5 Flash). Sub-second latency (250-400ms) prevents option premium slippage on BankNifty/Nifty, and high throughput avoids 429 quota exhaustion.\n"
            "2. Post-Market Synthesis & Journaling (After 15:30 IST): Use Gemini 4 Hydrogen. Its 1M token context window and 65k output limit enable full-day multi-trade log auditing and deep vector memory RAG ingestion.\n"
            "3. Quota Gate Warning: Never point live trading to unverified elemental preview models (Neon/Argon/Carbon on Free Tier) as zero-request limits trigger mid-session 429 execution lockouts."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "ai_infrastructure", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "journal_rule_post_mortem_20261119_moa_hybrid_routing",
        "document": (
            "Trader Rule #13 (19-Nov-2026 Lesson) — Mixture-of-Agents (MoA) F&O Model Router Architecture:\n"
            "To maximize alpha, reduce option slippage, and completely prevent 429 quota lockouts, decouple F&O intelligence tasks into specialized models:\n"
            "1. Live Market Scanning & Order Triggers: Gemini 3.8 Flash (sub-300ms latency ensures precision fill near trigger price).\n"
            "2. Greeks, IV Skew & Multi-Leg Spread Structuring: Gemini 4 Argon with immediate 3.8 Flash fallback (deep reasoning on delta/gamma pinning).\n"
            "3. High-Frequency Breaking News & Sentiment Filtering: Gemini 3.5 Flash / Flash-Lite (ultra-low latency binary classification).\n"
            "4. Post-Market Trade Auditing & Deep RAG Ingestion: Gemini 4 Hydrogen (1M token context for whole-day tick-by-tick log analysis).\n"
            "Rule: If any specialized route hits a rate-limit error, the engine must auto-fallback to Gemini 3.8 Flash within 50ms without dropping orders."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "moa_architecture", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "journal_rule_post_mortem_20261119_daily_expiry_rotation",
        "document": (
            "Trader Rule #14 (19-Nov-2026 Lesson) — 4-Day Daily Expiry F&O Rotation Protocol:\n"
            "Expand trading universe beyond BankNifty to all 4 high-liquidity NSE index derivatives with capital <= ₹7,616:\n"
            "1. Monday Expiry Priority: Midcap Nifty (^NSMIDCP, Lot 50, Step 25). Explosive gamma percentage expansion.\n"
            "2. Tuesday Expiry Priority: FinNifty (^CNXFIN, Lot 25, Step 50). Clean private banking + NBFC trending runs.\n"
            "3. Wednesday Expiry Priority: BankNifty (^NSEBANK, Lot 15, Step 100). High-volatility institutional scalping.\n"
            "4. Thursday Expiry Priority: Nifty 50 (^NSEI, Lot 25, Step 50). Macro heavyweight trend momentum.\n"
            "Execution Rule: Autonomous cycle evaluates the day's expiry index first, then scans remaining indices in parallel. Only the single highest-conviction setup (AI Conf >= 68%) is routed to Angel One (Max 1 active position)."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "multi_index_rotation", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "rule_15_profit_ladder_atr_trailing",
        "document": (
            "Trader Rule #15 (19-Nov-2026 Lesson) — Institutional F&O Profit Ladder & ATR Trailing Stop Architecture:\n"
            "Index options experience normal ±5% to ±8% noise on minor index fluctuations. Fixed 5% stops guarantee premature shakeouts.\n"
            "1. Adaptive Initial Stop-Loss: Set at -14.0% to -18.0% calibrated dynamically using 5m spot ATR (0.75 * ATR / Entry Price). Gives the trade space to develop while strictly capping total risk per lot under ₹450 (well below the daily ₹1,000 drawdown limit).\n"
            "2. Breakeven Lock (+18% to +20% Peak): When option reaches +18-20% gain, immediately ratchet SL to +1.5% net profit. The trade becomes 100% risk-free, guaranteeing that taxes, exchange fees, and STT are covered.\n"
            "3. Stage 1 Profit Lock (+30% Peak): Ratchet SL to +15% profit (locks in half the gain in the bank).\n"
            "4. Stage 2 Super-Runner (+50% Peak): Ratchet SL to +30% profit (locks in major runner gain).\n"
            "5. Stage 3 Mega-Gamma Trail (+75%+ Peak): Ratchet SL to Peak - 18% to capture parabolic 0DTE expiry squeezes without premature clock exits.\n"
            "6. Telegram Anti-Collision: Gracefully back off on HTTP 409 conflict so primary cloud instance maintains uninterrupted command & notification feed."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "profit_ladder_atr_exit", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "rule_16_delta_oi_trap_protection",
        "document": (
            "Trader Rule #16 (19-Nov-2026 Lesson) — Institutional Real-Time Delta OI Velocity & Trap Protection Protocol:\n"
            "Candle patterns frequently generate fake breakouts when retail traders chase price while institutional market makers aggressively build opposing option walls.\n"
            "1. Gate 5 Institutional Pre-Trade Veto: Before firing any BUY_CE or BUY_PE order, query the live broker option chain around ATM strikes.\n"
            "2. Put-Call Ratio (PCR) Boundaries: Block BUY_CE if PCR < 0.65 (heavy call writing ceiling). Block BUY_PE if PCR > 1.45 (heavy put writing floor cushion).\n"
            "3. Bull Trap Detection: If spot is moving up, but Delta CE OI expands > 35% faster than Delta PE OI, institutional writers are selling calls into the rally. Veto BUY_CE.\n"
            "4. Bear Trap Detection: If spot is falling, but Delta PE OI expands > 35% faster than Delta CE OI, institutional writers are selling puts into the drop. Veto BUY_PE.\n"
            "5. Short Covering & Squeeze Exemption: If Call writers are actively unwinding (Delta CE < 0) as spot approaches Call Wall, allow breakout execution to ride dealer short covering."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "delta_oi_trap_guard", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "rule_17_dynamic_moneyness_delta_selection",
        "document": (
            "Trader Rule #17 (19-Nov-2026 Lesson) — Dynamic Moneyness & Delta Strike Selection Architecture:\n"
            "Out-of-the-Money (OTM) options lose 100% of value to afternoon theta decay on 0DTE expiries and have sluggish delta (0.30 - 0.40).\n"
            "1. High-Conviction Trend Expansion (Conf >= 72% or Trending Regime): Dynamically select 1-Strike In-The-Money (Slight ITM, Delta ≈ 0.60):\n"
            "   - BUY_CE: strike = atm_strike - step (e.g. 57,800 CE when spot is 57,900).\n"
            "   - BUY_PE: strike = atm_strike + step (e.g. 58,000 PE when spot is 57,900).\n"
            "   Captures 60% of underlying spot movement immediately with built-in intrinsic value protection against theta decay.\n"
            "2. Nominal Scalping / Range Bound: Select strictly At-The-Money (ATM, Delta ≈ 0.50) strike.\n"
            "3. Elimination of Retail OTM Gambling: Deep OTM ('Hero or Zero') options are banned by the Quant architecture to preserve trading capital."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "dynamic_moneyness", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "rule_18_fractional_kelly_compounding",
        "document": (
            "Trader Rule #18 (19-Nov-2026 Lesson) — Fractional Kelly Capital Compounding & Dynamic Drawdown Guard:\n"
            "Static 1-lot trading permanently caps revenue potential as account equity grows, while excessive scaling during drawdown risks ruin.\n"
            "1. Fractional Kelly Exposure Ceiling: No single option trade may ever commit more than 40% of available cash balance.\n"
            "2. Preservation Phase (Cash <= ₹12,000): Enforce strict 1-Lot maximum (₹7,616 account baseline) to prioritize capital preservation.\n"
            "3. Growth Phase (Cash ₹12,000 - ₹20,000): Scale up to 2 Lots on high conviction (Conf >= 72%) if cost per lot fits within 40% cash ceiling.\n"
            "4. Compounding Phase (Cash >= ₹20,000): Scale up to 3 Lots on high conviction (Conf >= 75%).\n"
            "5. Dynamic Drawdown Guard (Anti-Martingale): If today's realized loss > ₹0, immediately force downsize position size back to 1 Lot.\n"
            "6. Dynamic Daily Loss Limit: Scales automatically to 10% of portfolio equity (floored at ₹1,000 minimum) to safeguard 90% of account equity."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "capital_compounding", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "rule_19_constituent_divergence_lunch_lull",
        "document": (
            "Trader Rule #19 (19-Nov-2026 Lesson) — Heavyweight Constituent Divergence, Midday Lockout & VIX Multiplier Protocol:\n"
            "1. Gate 6 Heavyweight Constituent Divergence Veto: HDFC Bank + ICICI Bank command 51.9% of Bank Nifty, and Reliance + HDFC Bank command 17.8% of Nifty 50. If top 2 heavyweight stocks diverge against the breakout (e.g. HDFC & ICICI both negative on BUY_CE), veto the signal as an institutional divergence trap.\n"
            "2. Midday Lunch-Lull Lockout (11:30 - 13:15 IST): Institutional volume drops by 65-70% before European markets open. Option entries are locked out unless accompanied by exceptional volume (>1.8x) and conviction (>= 82%), preserving cash for 13:15 Power-Hour.\n"
            "3. India VIX Strategy Multiplier: Low VIX (< 12.5) activates theta defense (+35% target, +14% breakeven); High VIX (> 18.0) widens trailing gap to 18% to absorb 100-point swings without premature shakeouts.\n"
            "4. Bid-Ask Spread Guard: Pauses execution 1.0s if option bid-ask spread friction exceeds 3.5%, avoiding instant market maker slippage."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "constituent_divergence_time_guard", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "trader_rule_20",
        "document": (
            "Trader Rule #20 (19-Nov-2026 Lesson) — Dual-Core Social Media & Real-Time News Sentiment Ingestion Protocol:\n"
            "1. Multi-Source Official RSS Ingestion: Replaced brittle HTML web scrapers with high-speed, rate-limit-immune official RSS feeds across Google News (Targeted Index & Retail Trader Sentiment queries), Economic Times (50 live market headlines), and Livemint (35 market/earnings feeds).\n"
            "2. Zero-Cost Dalal Street Financial Lexicon Engine: Weighted sentiment scoring calibrated specifically for Indian F&O (e.g. rate cut, FII inflow, breakout, 52-week high vs rate hike, FII dump, bloodbath, crash, margin call). Operates at zero latency and zero API cost.\n"
            "3. LLM Rate-Limit Immune Architecture: If Gemini API encounters HTTP 429 quota exhaustion or network timeout, the system seamlessly engages the zero-cost Financial Lexicon Engine with 100% uptime, eliminating blind-trading on macro event days."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "sentiment_social_news_protocol", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "trader_rule_21",
        "document": (
            "Trader Rule #21 (19-Nov-2026 Lesson) — Zero-Assumption Timezone & Market Hours Architecture:\n"
            "1. Cloud OS Timezone Bias Vulnerability: Cloud Linux VMs (Oracle, AWS, Docker) default system clocks to UTC/GMT. When market opens at 09:15 AM IST, the cloud clock reads 03:45 AM GMT. Python's naive datetime.now() interprets this as midnight/closed, completely silencing the autonomous trading engine during market hours.\n"
            "2. Permanent Operating System Sync: The host server must have timedatectl permanently locked to 'Asia/Kolkata' (IST, +0530).\n"
            "3. Code-Level Timezone Guarantee: All trading time checks, pre-market warmups, lunch-lull lockouts, and EOD square-offs must strictly invoke get_ist_now() using ZoneInfo('Asia/Kolkata'). Never rely on host server default clocks."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "timezone_resilience_protocol", "priority": "critical", "date": "2026-11-19"}
    },
    {
        "id": "trader_rule_22_session_auto_healing",
        "document": (
            "Trader Rule #22 (20-Nov-2026 Lesson) — 24/7 Cloud Session Auto-Healing & 08:45 AM Pre-Market Handshake Protocol:\n"
            "1. Midnight JWT Invalidation Vulnerability: Angel One SmartAPI invalidates all active JWT tokens every night at midnight (AB1007: Invalid Token / AG8003: Token missing). A long-running 24/7 daemon process can silently retain stale tokens, causing is_connected() or getProfile() to fail or return misleading statuses.\n"
            "2. Error Code Expansion: _is_session_expired_response() must explicitly recognize AB1007, AG8003, AB1010, AG8001, and AB1004 to trigger immediate force=True TOTP re-authentication on any broker API call.\n"
            "3. is_connected() Auto-Recovery: If profile verification fails or throws any network/auth exception, the client must trigger an immediate forced TOTP renewal rather than falling back to True on stale token strings.\n"
            "4. Automated 08:45 AM Pre-Market Daemon Reset: A root systemd cron (45 8 * * 1-5 /usr/bin/systemctl restart tradeverse) executes every weekday morning at 08:45 AM IST on the Oracle Cloud static IP (129.225.125.13). This cleans memory, executes a fresh TOTP handshake, downloads today's active NFO contracts, and guarantees the engine is 100% armed and ready for the 09:15:00 AM IST market bell."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "session_auto_healing_protocol", "priority": "critical", "date": "2026-11-20"}
    },
    {
        "id": "trader_rule_23_multi_account_copy_trading",
        "document": (
            "Trader Rule #23 (20-Nov-2026 Architectural Advancement) — Multi-Account Copy-Trading & Independent Margin Isolation Protocol:\n"
            "1. Isolated Capital Preservation: Multi-account copy-trading maintains strict capital isolation. Every active Angel One account calculates position sizing independently based strictly on its own available cash margin, never pooled or commingled.\n"
            "2. Fractional Kelly Sizing Per Account: Each account undergoes independent Kelly sizing guardrails: strict 1-lot preservation if available cash <= ₹12,000, 40% maximum single-trade margin ceiling, and immediate downsizing to 1 lot if nursing any daily loss.\n"
            "3. Simultaneous Parallel Fan-Out: When the AI Intraday Sniper generates a validated signal (>=68% confidence passing all 6 risk vetoes), limit-chase orders are dispatched to all active accounts simultaneously, ensuring identical entry prices and eliminating manual copy delay.\n"
            "4. Independent Trailing SL & Exit Orchestration: Stop-Loss (-15%), Target (+25%), Breakeven Locks (+1.5%), and EOD Auto Square-Off (15:20 IST) are tracked and executed per account key (account_id:symbol), ensuring one account's balance or execution status never impacts another."
        ),
        "metadata": {"author": "architect", "rule_type": "multi_account_copy_trading", "priority": "critical", "date": "2026-11-20"}
    },
    {
        "id": "journal_rule_early_momentum_unlock",
        "document": (
            "Trader Rule #24 (23-Nov-2026 Lesson) — 09:20 AM Early Momentum & 5m ORB Unlock Protocol:\n"
            "1. Two-Tier Market Open Protocol: Replaces the blunt 09:15-09:30 AM flat freeze. 09:15-09:20 IST (5 mins) acts as an Opening Spread Guard to absorb initial auction tick volatility and let option bid-ask spreads normalize.\n"
            "2. 09:20 AM Early Momentum Unlock: Once the 1st 5-minute candle closes (09:20 IST), high-conviction momentum signals (Confidence >= 75%) are fully permitted to execute live.\n"
            "3. Mega-Trend & Crash Capture: Prevents missing explosive morning breakdowns (such as the 23-Nov-2026 BankNifty 2,400-point collapse) while shielding capital from low-conviction opening whipsaws."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "early_momentum_unlock", "priority": "critical", "date": "2026-11-23"}
    },
    {
        "id": "journal_rule_breakeven_mtf_risk_integrity",
        "document": (
            "Trader Rule #25 (23-Nov-2026 Lesson) — Early Breakeven Lock (+10%), MTF Trend Anchor & Risk Dictionary Integrity:\n"
            "1. Early Breakeven Lock (+10% Peak): Lowers the breakeven ratchet trigger from +20% to +10.0% gain (locking Stop-Loss at +1.5% net profit). This renders winning trades 100% risk-free, covering taxes and STT, and eliminates profitable +12% trades from reversing into -15% stop-outs.\n"
            "2. 15-Minute Higher-Timeframe Trend Anchor: Resamples 5m bars into 15m intervals to calculate the 15m EMA-20 trend anchor. 5m Call entries are strictly vetoed if 15m trend is bearish; 5m Put entries are vetoed if 15m trend is bullish. Trend alignment awards a +5% confidence boost.\n"
            "3. Order Dictionary Parameter Integrity: Guarantees that 'confidence' and 'is_high_conviction' are always passed in order payloads from main.py to risk_engine.py, ensuring high-conviction crash/trend signals (>=75%) are never falsely blocked during market momentum windows."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "breakeven_mtf_risk_integrity", "priority": "critical", "date": "2026-11-23"}
    },
    {
        "id": "journal_rule_cluster_heartbeat_and_scaler_schema_lock",
        "document": (
            "Trader Rule #26 (25-Nov-2026 Lesson) — Automatic iMac-Cloud Heartbeat Failover & Scaler Feature Schema Lock:\n"
            "1. Zero-Split-Brain Heartbeat Election: When the local iMac engine is active, it broadcasts a 15-second SSH lease (45s TTL) to the Oracle Cloud VM (129.225.125.13). Oracle Cloud remains in HOT_STANDBY (pausing order entry, Angel One JWT polling, and Telegram getUpdates) while the lease is valid, and automatically promotes to ACTIVE_PRIMARY within 45s (or <1s on clean shutdown) whenever the iMac shuts down, sleeps, or loses connectivity.\n"
            "2. Sub-Model Scaler Schema Binding: TFTEngine and ModelEngine must always bind inference columns directly to self.scaler.feature_names_in_ with .reindex(columns=feats, fill_value=0.0) and isolate secondary TFT/RL sub-agent exceptions so independent retraining of daily/intraday ensembles never triggers a 500 feature-mismatch failure during market open."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "cluster_failover_and_schema_lock", "priority": "critical", "date": "2026-11-25"}
    },
    {
        "id": "journal_rule_post_audit_20261125_funnel_and_sebi_lot_sync",
        "document": (
            "Trader Rule #27 (25-Nov-2026 Post-Market Audit Optimization) — Intraday Gate-4 Timeframe Sync, True MIDCPNIFTY Index Alignment & SEBI Weekly Capital Routing:\n"
            "1. Gate 4 Timeframe Sync: When the 5m Intraday Sniper overrides a 1-Day HOLD signal with verified 5m/15m ORB momentum, analysis['model_scores']['technical'] must sync to the active 5m confluence score rather than retaining yesterday's 1D score (-1.0), which previously self-vetoed 97% of valid 5m BUY_CE setups (71.3% shadow win rate).\n"
            "2. True MIDCPNIFTY Underlying Mapping: NSE MIDCPNIFTY options track Nifty Midcap Select (NIFTY_MID_SELECT.NS / Angel token 99926074 at ~14,250, Lot 120), NOT Nifty Midcap 100 (^NSMIDCP at ~72,778). Option scrip resolution must strictly enforce exact strike+option_type suffix matching and never fall back to fuzzy futures candidates.\n"
            "3. SEBI 2026 Lot-Size & Risk-Cap Alignment: Enforce live NSE lot sizes (NIFTY=65 weekly, BANKNIFTY=30 monthly, FINNIFTY=60 monthly, MIDCPNIFTY=120 monthly). Bind OTM strike stepping strictly to RiskEngine.max_position_size (50% cash / ₹3,808.28 baseline) with universal NIFTY weekly option fallback when monthly index lots exceed capital limits.\n"
            "4. Multi-Layer Rate-Limit & Latency Shield: Enforce TTL caches across Angel One get_funds (20s), get_option_chain (10s), LTP (2s), ComponentLeaderEngine baskets (30s, including dedicated MIDCPNIFTY leaders BSE/DIXON/PERSISTENT/COFORGE/POLYCAB), and DataPipeline CSV fetches (45s intraday / 15m daily)."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "funnel_and_sebi_lot_optimization", "priority": "critical", "date": "2026-11-25"}
    },
    {
        "id": "journal_rule_20261125_full_fno_microstructure_gates",
        "document": (
            "Trader Rule #28 (25-Nov-2026 Institutional F&O Microstructure Completion) — 5-Depth Option Quotes, Minimum Delta Floor, IV-Crush Veto & Futures Basis Gate:\n"
            "1. AngelClient.quote() 5-Depth Microstructure: Queries SmartAPI getMarketData('FULL') with 2s micro-caching to feed real 5-level NFO option bid/ask spreads and L2 order-book imbalance into SmartExecutionEngine (>3.5% pause, >5.0% illiquidity veto).\n"
            "2. Minimum |Delta| Floor on OTM Capital-Fit Stepping: Calculates exact Black-Scholes Greeks using ScripMaster contract DTE. Stops monthly OTM stepping below |Delta| 0.28 and rejects any fallback contract below |Delta| 0.25 to eliminate deep-OTM theta-decay lottery trades.\n"
            "3. Gate 7 Front-Month Futures Basis & Buildup Guard: Tracks live NIFTY/BANKNIFTY/FINNIFTY/MIDCPNIFTY front-month futures basis (Fut - Spot) and ΔOI buildup. Vetoes BUY_CE during steep futures backwardation (< -0.20% discount trap) or active institutional Short Buildup, and vetoes BUY_PE into strong institutional Long Buildup (> +0.90% premium).\n"
            "4. Gate 8 Contract IV-Crush Protection: Solves exact strike Implied Volatility (Newton-Raphson) + 252-day IV Percentile before execution, vetoing naked option buys when contract IV is severely bloated (> max(42%, 2.35x VIX) at IVP > 85%)."
        ),
        "metadata": {"author": "post_mortem", "rule_type": "fno_microstructure_and_greeks_guard", "priority": "critical", "date": "2026-11-25"}
    }
]


class TradeverseRAGEngine:
    """
    Manages embedded ChromaDB vector collections, knowledge ingestion,
    and semantic context retrieval for Tradeverse AI Assistant.
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self.client = None
        self.collections: Dict[str, Any] = {}
        self.initialized = False
        self._initialize_db()

    def _initialize_db(self):
        """Initializes persistent ChromaDB client and collections."""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

            # Initialize each collection
            for col_name in COLLECTIONS:
                col = self.client.get_or_create_collection(
                    name=col_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections[col_name] = col

            self.initialized = True
            logger.info(f"✅ Tradeverse RAG Vector Engine initialized at: {self.persist_dir}")

            # Check if seed documents need to be added
            self._seed_default_knowledge()

        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB RAG engine: {e}")
            self.initialized = False

    def _seed_default_knowledge(self):
        """Seeds initial curated quant knowledge if collections are empty."""
        try:
            seeds = {
                "trading_playbook": SEED_PLAYBOOK,
                "historical_regimes": SEED_REGIMES,
                "banking_research": SEED_BANKING,
                "trader_journal": SEED_JOURNAL
            }

            for col_name, seed_items in seeds.items():
                col = self.collections.get(col_name)
                if col and col.count() < len(seed_items):
                    ids = [item["id"] for item in seed_items]
                    docs = [item["document"] for item in seed_items]
                    metas = [item["metadata"] for item in seed_items]

                    col.upsert(ids=ids, documents=docs, metadatas=metas)
                    logger.info(f"📚 Synced {len(ids)} seed documents into '{col_name}' collection.")
        except Exception as e:
            logger.warning(f"⚠️ Warning seeding knowledge base: {e}")

    def query_rag(
        self,
        query_text: str,
        collection_name: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Queries one or all collections for semantically relevant knowledge.
        
        Returns:
            List of matching records with id, document, metadata, and distance.
        """
        if not self.initialized or not self.client:
            logger.warning("RAG engine not initialized for query.")
            return []

        results = []
        target_cols = [collection_name] if collection_name and collection_name in self.collections else list(self.collections.keys())

        for c_name in target_cols:
            col = self.collections.get(c_name)
            if not col or col.count() == 0:
                continue

            try:
                n_res = min(top_k, col.count())
                query_res = col.query(
                    query_texts=[query_text],
                    n_results=n_res
                )

                if query_res and query_res.get("documents") and query_res["documents"][0]:
                    docs = query_res["documents"][0]
                    metas = query_res.get("metadatas", [[]])[0]
                    ids = query_res.get("ids", [[]])[0]
                    dists = query_res.get("distances", [[]])[0]

                    for i in range(len(docs)):
                        dist = dists[i] if i < len(dists) else 0.5
                        sim_score = max(0.0, round(1.0 - dist, 3))
                        results.append({
                            "collection": c_name,
                            "id": ids[i] if i < len(ids) else f"{c_name}_{i}",
                            "document": docs[i],
                            "metadata": metas[i] if i < len(metas) else {},
                            "similarity_score": sim_score,
                            "distance": round(dist, 4)
                        })
            except Exception as e:
                logger.error(f"Error querying collection '{c_name}': {e}")

        # Sort combined results by similarity score (highest first)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def add_document(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        collection_name: str = "trader_journal",
        doc_id: Optional[str] = None
    ) -> Dict:
        """
        Adds a new document to a specified vector collection.
        """
        if not self.initialized:
            return {"status": "error", "message": "RAG Engine not initialized"}

        if collection_name not in self.collections:
            return {"status": "error", "message": f"Collection '{collection_name}' does not exist"}

        import uuid
        generated_id = doc_id or f"{collection_name}_{uuid.uuid4().hex[:8]}"
        meta = metadata or {"source": "user_ui"}

        try:
            col = self.collections[collection_name]
            col.add(ids=[generated_id], documents=[content], metadatas=[meta])
            logger.info(f"📝 Added document '{generated_id}' to collection '{collection_name}'")
            return {
                "status": "success",
                "id": generated_id,
                "collection": collection_name,
                "total_count": col.count()
            }
        except Exception as e:
            logger.error(f"Failed to add document to RAG: {e}")
            return {"status": "error", "message": str(e)}

    def build_rag_context(
        self,
        query_text: str,
        symbol: str = "NSE:BANKNIFTY",
        trade_type: Optional[str] = None,
        top_k: int = 3
    ) -> str:
        """
        Constructs a structured RAG context block formatted for LLM system/user prompts.
        """
        enriched_query = f"{symbol} {trade_type or ''} {query_text}".strip()
        matches = self.query_rag(enriched_query, top_k=top_k)

        if not matches:
            return ""

        context_lines = ["\n[RETRIEVED QUANTITATIVE KNOWLEDGE BASE & PLAYBOOK MEMORY]:"]
        for idx, match in enumerate(matches, 1):
            category = match.get("collection", "general").upper().replace("_", " ")
            score = match.get("similarity_score", 0.0)
            context_lines.append(
                f"\n--- SOURCE #{idx}: [{category}] (Relevance: {score * 100:.1f}%) ---\n"
                f"{match['document']}"
            )

        context_lines.append("\n[END OF KNOWLEDGE BASE CONTEXT]\n")
        return "\n".join(context_lines)

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic statistics for all vector collections."""
        if not self.initialized:
            return {"status": "offline", "collections": {}, "total_documents": 0}

        col_stats = {}
        total = 0
        for name, col in self.collections.items():
            cnt = col.count()
            col_stats[name] = cnt
            total += cnt

        return {
            "status": "active",
            "storage_path": self.persist_dir,
            "total_documents": total,
            "collections": col_stats
        }


# Singleton instance
rag_engine = TradeverseRAGEngine()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("⚡ TESTING TRADEVERSE RAG ENGINE")
    print("=" * 60)
    stats = rag_engine.get_stats()
    print("Stats:", stats)

    print("\n🔍 Querying Playbook for 'Gamma Wall breakout'...")
    results = rag_engine.query_rag("How to trade Gamma Wall breakout on BankNifty?", top_k=2)
    for r in results:
        print(f"\n[{r['collection']}] (Score: {r['similarity_score']}):")
        print(r['document'])

    print("\n📝 Testing Dynamic Prompt Context Generation...")
    context = rag_engine.build_rag_context("Should I buy Bank Nifty calls at Call Wall?")
    print(context)
    print("=" * 60 + "\n")
