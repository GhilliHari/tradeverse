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
                if col and col.count() == 0:
                    ids = [item["id"] for item in seed_items]
                    docs = [item["document"] for item in seed_items]
                    metas = [item["metadata"] for item in seed_items]

                    col.add(ids=ids, documents=docs, metadatas=metas)
                    logger.info(f"📚 Seeded {len(ids)} documents into '{col_name}' collection.")
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
