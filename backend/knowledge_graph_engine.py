"""
Tradeverse Financial & Quantitative Knowledge Graph Engine.
Persistent, embedded in-process NetworkX MultiDiGraph mapping:
1. Index & Constituent Weight Hierarchies (Bank Nifty, HDFC, ICICI, SBI, Kotak)
2. Macroeconomic Transmission Channels (RBI MPC, Repo, CRR, Bond Yields, Crude, FII)
3. Derivatives & Option Microstructure (Call/Put OI, GEX Walls, Squeezes, Max Pain)
4. Quantitative Strategies & Price Action Mechanics (CPR, VWAP, Gann, CVD Divergence)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import networkx as nx

logger = logging.getLogger("tradeverse.graph")

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
GRAPH_PERSIST_FILE = os.path.join(KNOWLEDGE_BASE_DIR, "graph_db.json")

os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

# Curated Seed Nodes for Financial & Quant Knowledge Graph
SEED_NODES = [
    # 1. Indices
    {
        "id": "BANKNIFTY",
        "label": "Bank Nifty Index",
        "category": "index",
        "color": "#06b6d4",
        "properties": {"exchange": "NSE", "asset_class": "equity_index", "lot_size": 15, "strike_step": 100}
    },
    {
        "id": "NIFTY50",
        "label": "Nifty 50 Index",
        "category": "index",
        "color": "#0ea5e9",
        "properties": {"exchange": "NSE", "asset_class": "broad_index", "lot_size": 25, "strike_step": 50}
    },

    # 2. Banking Heavyweight Constituents
    {
        "id": "HDFCBANK",
        "label": "HDFC Bank (HDFCBANK.NS)",
        "category": "bank_stock",
        "color": "#3b82f6",
        "properties": {"weight": 0.29, "sector": "private_bank", "beta": 1.15, "nim_target": "3.5-3.7%"}
    },
    {
        "id": "ICICIBANK",
        "label": "ICICI Bank (ICICIBANK.NS)",
        "category": "bank_stock",
        "color": "#6366f1",
        "properties": {"weight": 0.23, "sector": "private_bank", "beta": 1.25, "roa": ">2.2%"}
    },
    {
        "id": "SBIN",
        "label": "State Bank of India (SBIN.NS)",
        "category": "bank_stock",
        "color": "#8b5cf6",
        "properties": {"weight": 0.10, "sector": "psu_bank", "beta": 1.30, "govt_holding": "57%"}
    },
    {
        "id": "KOTAKBANK",
        "label": "Kotak Mahindra Bank (KOTAKBANK.NS)",
        "category": "bank_stock",
        "color": "#a855f7",
        "properties": {"weight": 0.10, "sector": "private_bank", "beta": 0.95, "car": "20.8%"}
    },
    {
        "id": "AXISBANK",
        "label": "Axis Bank (AXISBANK.NS)",
        "category": "bank_stock",
        "color": "#d946ef",
        "properties": {"weight": 0.08, "sector": "private_bank", "beta": 1.35}
    },
    {
        "id": "INDUSINDBK",
        "label": "IndusInd Bank (INDUSINDBK.NS)",
        "category": "bank_stock",
        "color": "#ec4899",
        "properties": {"weight": 0.05, "sector": "private_bank", "beta": 1.45}
    },

    # 3. Macro & Regulatory Policy Nodes
    {
        "id": "RBI_MPC",
        "label": "RBI Monetary Policy Committee",
        "category": "macro_policy",
        "color": "#f59e0b",
        "properties": {"frequency": "bi_monthly", "mandate": "inflation_targeting_4pct", "announcement_time": "10:00 AM IST"}
    },
    {
        "id": "REPO_RATE",
        "label": "RBI Repo Benchmark Rate",
        "category": "macro_policy",
        "color": "#f97316",
        "properties": {"current_rate": "6.50%", "sensitivity": "high_bank_margins"}
    },
    {
        "id": "CASH_RESERVE_RATIO_CRR",
        "label": "Cash Reserve Ratio (CRR)",
        "category": "macro_policy",
        "color": "#ef4444",
        "properties": {"current_ratio": "4.50%", "impact": "banking_system_liquidity"}
    },
    {
        "id": "INDIA_10Y_BOND_YIELD",
        "label": "India 10Y Sovereign Bond Yield",
        "category": "macro_policy",
        "color": "#fbbf24",
        "properties": {"benchmark": "IN10Y", "impact": "psu_treasury_mark_to_market"}
    },
    {
        "id": "USDINR",
        "label": "USD / INR Currency Rate",
        "category": "macro_policy",
        "color": "#eab308",
        "properties": {"pair": "USDINR", "impact": "fii_capital_flow_direction"}
    },
    {
        "id": "BRENT_CRUDE",
        "label": "Brent Crude Oil",
        "category": "macro_policy",
        "color": "#84cc16",
        "properties": {"import_dependency": "85%", "inflation_transmission": "rapid"}
    },
    {
        "id": "FII_DII_FLOWS",
        "label": "Institutional FII & DII Flows",
        "category": "macro_policy",
        "color": "#10b981",
        "properties": {"flow_tracker": "daily_cash_derivatives", "impact": "trend_sustainability"}
    },

    # 4. GEX & Option Market Microstructure
    {
        "id": "UPPER_GAMMA_WALL",
        "label": "Upper Gamma Wall (Call Wall)",
        "category": "derivatives_gex",
        "color": "#f43f5e",
        "properties": {"metric": "max_positive_call_gamma", "dealer_role": "net_short_gamma_sellers", "behavior": "strong_ceiling_barrier"}
    },
    {
        "id": "LOWER_GAMMA_WALL",
        "label": "Lower Gamma Wall (Put Wall)",
        "category": "derivatives_gex",
        "color": "#10b981",
        "properties": {"metric": "max_positive_put_gamma", "dealer_role": "net_long_gamma_buyers", "behavior": "strong_floor_support"}
    },
    {
        "id": "CALL_OI_UNWINDING",
        "label": "Call Open Interest Unwinding",
        "category": "derivatives_gex",
        "color": "#fb7185",
        "properties": {"trigger": "call_writers_covering", "sentiment": "bullish_catalyst"}
    },
    {
        "id": "GAMMA_SHORT_SQUEEZE",
        "label": "Gamma Short Squeeze Expansion",
        "category": "derivatives_gex",
        "color": "#38bdf8",
        "properties": {"velocity": "400-800 pts in 45m", "mechanism": "dealer_delta_rehedging_futures"}
    },
    {
        "id": "MAX_PAIN_PINNING",
        "label": "Option Max Pain Strike Pinning",
        "category": "derivatives_gex",
        "color": "#a78bfa",
        "properties": {"timeframe": "expiry_day_after_2pm", "effect": "draws_price_to_minimum_loss_strike"}
    },
    {
        "id": "WEEKEND_THETA_DECAY",
        "label": "Weekend Theta Decay Penalty",
        "category": "derivatives_gex",
        "color": "#f87171",
        "properties": {"timeframe": "friday_afternoon", "decay_rate": "25-35% premium loss by monday open"}
    },

    # 5. Quantitative Strategies & Price Action Mechanics
    {
        "id": "NARROW_CPR",
        "label": "Narrow CPR (Central Pivot Range)",
        "category": "quant_strategy",
        "color": "#22c55e",
        "properties": {"width": "<0.25% index price", "prediction": "high_momentum_trending_day", "win_rate": 0.78}
    },
    {
        "id": "VIRGIN_CPR",
        "label": "Virgin CPR Magnet Level",
        "category": "quant_strategy",
        "color": "#14b8a6",
        "properties": {"status": "untested_in_prior_session", "behavior": "high_probability_reversal_target"}
    },
    {
        "id": "VWAP_BAND",
        "label": "VWAP & 20 EMA Confluence Band",
        "category": "quant_strategy",
        "color": "#06b6d4",
        "properties": {"metric": "volume_weighted_benchmark", "strategy": "pullback_continuation"}
    },
    {
        "id": "CVD_ABSORPTION",
        "label": "Cumulative Volume Delta (CVD) Absorption",
        "category": "quant_strategy",
        "color": "#c084fc",
        "properties": {"indicator": "cvd_divergence", "signal": "institutional_limit_order_absorption"}
    },
    {
        "id": "GANN_90_HARMONIC",
        "label": "Gann 90° & 180° Harmonic Levels",
        "category": "quant_strategy",
        "color": "#e879f9",
        "properties": {"formula": "square_of_9", "reversal_points": "90deg and 180deg price steps"}
    },
    {
        "id": "HARD_STOP_LOSS",
        "label": "Hard Stop-Loss & 1% Risk Rule",
        "category": "quant_strategy",
        "color": "#ef4444",
        "properties": {"rule": "max_1pct_capital_per_trade", "discipline": "never_widen_losing_sl"}
    }
]

# Curated Seed Edges (Relationships with weights & typed predicates)
SEED_EDGES = [
    # Constituent Weight Relations to Bank Nifty (Combined ~85% weight)
    {"source": "HDFCBANK", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.29, "description": "Primary heavyweight driver (29% weight)"},
    {"source": "ICICIBANK", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.23, "description": "Momentum leader constituent (23% weight)"},
    {"source": "SBIN", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.10, "description": "PSU banking bellwether (10% weight)"},
    {"source": "KOTAKBANK", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.10, "description": "Asset quality & capital strength anchor (10% weight)"},
    {"source": "AXISBANK", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.08, "description": "High beta private bank (8% weight)"},
    {"source": "INDUSINDBK", "target": "BANKNIFTY", "relation": "CONSTITUENT_OF", "weight": 0.05, "description": "High beta retail constituent (5% weight)"},

    # Macro & Regulatory Transmission Paths
    {"source": "RBI_MPC", "target": "REPO_RATE", "relation": "SETS_BENCHMARK", "weight": 1.0, "description": "Sets benchmark repo borrowing rate"},
    {"source": "RBI_MPC", "target": "CASH_RESERVE_RATIO_CRR", "relation": "MANDATES", "weight": 1.0, "description": "Mandates mandatory cash reserve ratio"},
    {"source": "REPO_RATE", "target": "HDFCBANK", "relation": "IMPACTS_NIM", "weight": 0.85, "description": "Rate cuts expand credit demand; hikes compress NIM margins"},
    {"source": "REPO_RATE", "target": "ICICIBANK", "relation": "IMPACTS_NIM", "weight": 0.80, "description": "Direct transmission to floating loan yields"},
    {"source": "CASH_RESERVE_RATIO_CRR", "target": "SBIN", "relation": "LOCKS_LIQUIDITY", "weight": 0.90, "description": "Higher CRR impounds loanable funds at 0% return"},
    {"source": "CASH_RESERVE_RATIO_CRR", "target": "HDFCBANK", "relation": "LOCKS_LIQUIDITY", "weight": 0.85, "description": "Reduces bank lending capacity"},
    {"source": "INDIA_10Y_BOND_YIELD", "target": "SBIN", "relation": "IMPACTS_TREASURY", "weight": 0.88, "description": "Yield surges cause mark-to-market bond portfolio losses"},
    {"source": "BRENT_CRUDE", "target": "USDINR", "relation": "PRESSURES_CURRENCY", "weight": 0.75, "description": "Higher oil import bills weaken rupee against USD"},
    {"source": "USDINR", "target": "FII_DII_FLOWS", "relation": "DRIVES_CAPITAL_FLOW", "weight": 0.80, "description": "Rupee depreciation triggers FII equity selling"},
    {"source": "FII_DII_FLOWS", "target": "BANKNIFTY", "relation": "DRIVES_INSTITUTIONAL_LIQUIDITY", "weight": 0.85, "description": "FII net buying drives large-cap banking index trends"},

    # Derivatives, GEX Walls & Microstructure Paths
    {"source": "UPPER_GAMMA_WALL", "target": "BANKNIFTY", "relation": "CREATES_CEILING", "weight": 0.90, "description": "Dealer call selling dampens price advance"},
    {"source": "LOWER_GAMMA_WALL", "target": "BANKNIFTY", "relation": "CREATES_FLOOR", "weight": 0.90, "description": "Dealer put buying absorbs market sell-offs"},
    {"source": "CALL_OI_UNWINDING", "target": "UPPER_GAMMA_WALL", "relation": "DESTABILIZES_WALL", "weight": 0.85, "description": "Call covering removes resistance barrier"},
    {"source": "UPPER_GAMMA_WALL", "target": "GAMMA_SHORT_SQUEEZE", "relation": "TRIGGER_ON_BREACH", "weight": 0.92, "description": "Wall breach forces explosive dealer delta re-hedging"},
    {"source": "GAMMA_SHORT_SQUEEZE", "target": "BANKNIFTY", "relation": "VERTICAL_PRICE_EXPANSION", "weight": 0.95, "description": "Forces vertical 400-800 point index surge in Bank Nifty"},
    {"source": "MAX_PAIN_PINNING", "target": "BANKNIFTY", "relation": "EXPIRY_MAGNET", "weight": 0.75, "description": "Draws index towards minimum option loss strike after 2:00 PM"},
    {"source": "WEEKEND_THETA_DECAY", "target": "UPPER_GAMMA_WALL", "relation": "ERODES_OUT_OF_MONEY", "weight": 0.80, "description": "Destroys naked OTM premium over non-trading weekend"},

    # Quantitative Strategies & Setup Confluences
    {"source": "NARROW_CPR", "target": "BANKNIFTY", "relation": "FORECASTS_TREND_DAY", "weight": 0.78, "description": "Predicts >500 point high-velocity breakout session"},
    {"source": "VIRGIN_CPR", "target": "BANKNIFTY", "relation": "ACTS_AS_MAGNETIC_TARGET", "weight": 0.82, "description": "High probability mean-reversion target"},
    {"source": "VWAP_BAND", "target": "BANKNIFTY", "relation": "PULLBACK_ENTRY_BAND", "weight": 0.80, "description": "Optimal institutional risk-reward entry zone"},
    {"source": "CVD_ABSORPTION", "target": "UPPER_GAMMA_WALL", "relation": "CONFIRMS_RESISTANCE_REVERSAL", "weight": 0.84, "description": "Confirms large limit orders absorbing breakout buyers"},
    {"source": "GANN_90_HARMONIC", "target": "BANKNIFTY", "relation": "PROVIDES_SQUARE_OF_9_TARGET", "weight": 0.76, "description": "Calculates harmonic price-time target levels"},
    {"source": "HARD_STOP_LOSS", "target": "BANKNIFTY", "relation": "CAPITAL_PRESERVATION_BOUNDARY", "weight": 1.0, "description": "Enforces strict 1% account risk cap"}
]


class TradeverseKnowledgeGraph:
    """
    In-memory NetworkX MultiDiGraph manager with JSON persistence,
    multi-hop path finding, subgraph extraction, and GraphRAG context building.
    """

    def __init__(self, persist_file: str = GRAPH_PERSIST_FILE):
        self.persist_file = persist_file
        self.graph = nx.MultiDiGraph()
        self._load_or_seed_graph()

    def _load_or_seed_graph(self):
        """Loads graph from JSON or seeds initial financial graph."""
        if os.path.exists(self.persist_file):
            try:
                with open(self.persist_file, "r") as f:
                    data = json.load(f)
                
                self.graph.clear()
                for node in data.get("nodes", []):
                    self.graph.add_node(node["id"], **node)
                
                for edge in data.get("edges", []):
                    self.graph.add_edge(
                        edge["source"],
                        edge["target"],
                        key=edge.get("relation", "RELATED_TO"),
                        **edge
                    )
                logger.info(f"🕸️ Loaded Knowledge Graph from {self.persist_file} ({self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges)")
                return
            except Exception as e:
                logger.warning(f"Failed to load graph JSON, re-seeding: {e}")

        # Seed initial graph
        self._seed_default_graph()

    def _seed_default_graph(self):
        """Builds and persists default financial/quant knowledge graph."""
        self.graph.clear()

        for node in SEED_NODES:
            self.graph.add_node(node["id"], **node)

        for edge in SEED_EDGES:
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                key=edge.get("relation", "RELATED_TO"),
                **edge
            )

        self._save_to_json()
        logger.info(f"✅ Initialized and persisted Tradeverse Knowledge Graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def _save_to_json(self):
        """Serializes the graph to JSON file."""
        try:
            data = self.get_graph_data()
            with open(self.persist_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist graph to JSON: {e}")

    def get_graph_data(self, live_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Returns full graph serialized for visualization and API responses,
        enriched with actual real-time market quotes and GEX metrics.
        """
        nodes_list = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_copy = attrs.copy()
            node_copy["id"] = node_id
            if live_data and node_id in live_data:
                node_copy["live_data"] = live_data[node_id]
            nodes_list.append(node_copy)

        edges_list = []
        for u, v, key, attrs in self.graph.edges(keys=True, data=True):
            edge_copy = attrs.copy()
            edge_copy["source"] = u
            edge_copy["target"] = v
            edge_copy["relation"] = key
            edges_list.append(edge_copy)

        categories = list(set([n.get("category", "general") for n in nodes_list]))

        return {
            "nodes": nodes_list,
            "edges": edges_list,
            "stats": {
                "total_nodes": len(nodes_list),
                "total_edges": len(edges_list),
                "categories": categories
            }
        }

    def get_entity_subgraph(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Extracts an egocentric subgraph around a specific entity up to depth N.
        """
        if entity_id not in self.graph:
            return {"nodes": [], "edges": [], "error": f"Entity '{entity_id}' not in graph"}

        # Use BFS to discover nodes within radius = depth
        discovered_nodes = {entity_id}
        current_layer = {entity_id}

        for _ in range(depth):
            next_layer = set()
            for n in current_layer:
                # Predecessors (incoming) + Successors (outgoing)
                next_layer.update(self.graph.predecessors(n))
                next_layer.update(self.graph.successors(n))
            discovered_nodes.update(next_layer)
            current_layer = next_layer

        sub_g = self.graph.subgraph(discovered_nodes)

        sub_nodes = []
        for node_id, attrs in sub_g.nodes(data=True):
            n_copy = attrs.copy()
            n_copy["id"] = node_id
            sub_nodes.append(n_copy)

        sub_edges = []
        for u, v, key, attrs in sub_g.edges(keys=True, data=True):
            e_copy = attrs.copy()
            e_copy["source"] = u
            e_copy["target"] = v
            e_copy["relation"] = key
            sub_edges.append(e_copy)

        return {
            "entity": entity_id,
            "depth": depth,
            "nodes": sub_nodes,
            "edges": sub_edges,
            "total_nodes": len(sub_nodes),
            "total_edges": len(sub_edges)
        }

    def find_causal_path(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        Finds shortest multi-hop causal reasoning path between source and target nodes.
        """
        if source_id not in self.graph or target_id not in self.graph:
            return {
                "found": False,
                "path": [],
                "hops": 0,
                "message": f"One or both entities ('{source_id}', '{target_id}') not found in graph."
            }

        try:
            # Simple directed shortest path
            path_nodes = nx.shortest_path(self.graph, source=source_id, target=target_id)
            
            # Extract edge details along path
            path_edges = []
            for i in range(len(path_nodes) - 1):
                u = path_nodes[i]
                v = path_nodes[i+1]
                edge_data = self.graph.get_edge_data(u, v)
                # Take first edge in multigraph
                first_key = list(edge_data.keys())[0] if edge_data else "RELATED_TO"
                attrs = edge_data[first_key] if edge_data else {}
                path_edges.append({
                    "source": u,
                    "target": v,
                    "relation": first_key,
                    "description": attrs.get("description", ""),
                    "weight": attrs.get("weight", 1.0)
                })

            return {
                "found": True,
                "source": source_id,
                "target": target_id,
                "hops": len(path_nodes) - 1,
                "path_nodes": path_nodes,
                "path_edges": path_edges
            }
        except nx.NetworkXNoPath:
            # Try undirected path fallback for connectivity check
            undirected_g = self.graph.to_undirected()
            if nx.has_path(undirected_g, source_id, target_id):
                u_path = nx.shortest_path(undirected_g, source_id, target_id)
                return {
                    "found": True,
                    "is_bidirectional": True,
                    "hops": len(u_path) - 1,
                    "path_nodes": u_path,
                    "path_edges": [],
                    "note": "Connected via multi-hop market feedback loop (bi-directional)"
                }
            return {
                "found": False,
                "path": [],
                "hops": 0,
                "message": f"No causal path found between '{source_id}' and '{target_id}'."
            }

    def build_graph_context(self, query: str, symbol: str = "NSE:BANKNIFTY") -> str:
        """
        Constructs a structured GraphRAG context block containing relevant
        entity triples and multi-hop paths to enrich Gemini prompts.
        """
        q_upper = query.upper()
        norm_symbol = symbol.replace("NSE:", "").upper()
        
        # Identify matching entities in query
        matched_entities = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_label = attrs.get("label", "").upper()
            if node_id in q_upper or any(word in q_upper for word in node_id.split("_")):
                matched_entities.append(node_id)
            elif node_label and any(term in q_upper for term in node_label.split() if len(term) > 3):
                matched_entities.append(node_id)

        # Always include active index symbol
        if norm_symbol in self.graph and norm_symbol not in matched_entities:
            matched_entities.append(norm_symbol)
        if "BANKNIFTY" in self.graph and "BANKNIFTY" not in matched_entities:
            matched_entities.append("BANKNIFTY")

        triples = []
        visited_edges = set()

        for entity in matched_entities[:4]:
            # Outgoing relations
            for target in self.graph.successors(entity):
                for key, data in self.graph.get_edge_data(entity, target).items():
                    edge_tuple = (entity, key, target)
                    if edge_tuple not in visited_edges:
                        visited_edges.add(edge_tuple)
                        desc = data.get("description", "")
                        weight = data.get("weight")
                        weight_str = f" [Weight/Conf: {weight}]" if weight is not None else ""
                        triples.append(f"• ({entity}) --[{key}]--> ({target}){weight_str}: {desc}")

            # Incoming relations
            for source in self.graph.predecessors(entity):
                for key, data in self.graph.get_edge_data(source, entity).items():
                    edge_tuple = (source, key, entity)
                    if edge_tuple not in visited_edges:
                        visited_edges.add(edge_tuple)
                        desc = data.get("description", "")
                        triples.append(f"• ({source}) --[{key}]--> ({entity}): {desc}")

        if not triples:
            return ""

        context_header = "\n[STRUCTURED KNOWLEDGE GRAPH & CAUSAL TRANSMISSION PATHS]:"
        context_body = "\n".join(triples[:12])
        context_footer = "\n[END OF KNOWLEDGE GRAPH CONTEXT]\n"

        return f"{context_header}\n{context_body}{context_footer}"

    def add_node(self, node_id: str, label: str, category: str = "custom", properties: Optional[Dict] = None) -> Dict:
        """Adds or updates a node in the graph."""
        props = properties or {}
        self.graph.add_node(node_id, id=node_id, label=label, category=category, properties=props)
        self._save_to_json()
        logger.info(f"Node '{node_id}' added to Knowledge Graph.")
        return {"status": "success", "node_id": node_id, "total_nodes": self.graph.number_of_nodes()}

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0, description: str = "") -> Dict:
        """Adds a directed relation between two nodes."""
        if source not in self.graph or target not in self.graph:
            return {"status": "error", "message": "Source or target node does not exist in graph"}

        self.graph.add_edge(source, target, key=relation, relation=relation, weight=weight, description=description)
        self._save_to_json()
        logger.info(f"Edge ({source}) -[{relation}]-> ({target}) added to Knowledge Graph.")
        return {"status": "success", "source": source, "target": target, "relation": relation, "total_edges": self.graph.number_of_edges()}


# Singleton instance
knowledge_graph = TradeverseKnowledgeGraph()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🕸️ TESTING TRADEVERSE KNOWLEDGE GRAPH ENGINE")
    print("=" * 60)
    data = knowledge_graph.get_graph_data()
    print(f"Nodes: {data['stats']['total_nodes']} | Edges: {data['stats']['total_edges']}")
    print("Categories:", data['stats']['categories'])

    print("\n🔍 Testing Multi-Hop Path: RBI_MPC -> BANKNIFTY...")
    path = knowledge_graph.find_causal_path("RBI_MPC", "BANKNIFTY")
    print("Found:", path.get("found"), f"({path.get('hops')} hops)")
    for edge in path.get("path_edges", []):
        print(f"  ({edge['source']}) --[{edge['relation']}]--> ({edge['target']}): {edge['description']}")

    print("\n🔍 Testing Subgraph around HDFCBANK (depth=1)...")
    subgraph = knowledge_graph.get_entity_subgraph("HDFCBANK", depth=1)
    print(f"Subgraph Nodes ({subgraph['total_nodes']}):", [n['id'] for n in subgraph['nodes']])

    print("\n📝 Testing GraphRAG Prompt Context Generation...")
    ctx = knowledge_graph.build_graph_context("How does RBI repo rate change affect HDFC Bank and Bank Nifty?")
    print(ctx)
    print("=" * 60 + "\n")
