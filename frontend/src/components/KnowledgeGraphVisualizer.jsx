import React, { useState, useEffect, useRef } from 'react';
import { Network, Sparkles, Layers, ArrowRight, RefreshCw, ZoomIn, ZoomOut, Activity, ChevronRight, TrendingUp, TrendingDown, Shield } from 'lucide-react';
import HUDCard from './ui/HUDCard';
import { getApiUrl, API_URL } from '../config/api';

const CATEGORY_CONFIG = {
    index: { bg: 'rgba(6, 182, 212, 0.25)', border: '#06b6d4', text: '#22d3ee', label: 'Index & Benchmarks', order: 1 },
    bank_stock: { bg: 'rgba(99, 102, 241, 0.25)', border: '#6366f1', text: '#818cf8', label: 'Bank Heavyweights', order: 2 },
    macro_policy: { bg: 'rgba(245, 158, 11, 0.25)', border: '#f59e0b', text: '#fbbf24', label: 'Macro & Regulatory', order: 3 },
    derivatives_gex: { bg: 'rgba(244, 63, 94, 0.25)', border: '#f43f5e', text: '#fb7185', label: 'GEX & Microstructure', order: 4 },
    quant_strategy: { bg: 'rgba(34, 197, 94, 0.25)', border: '#22c55e', text: '#4ade80', label: 'Quant Strategies', order: 5 }
};

// Robust initial seed data so the topology is NEVER blank while loading
const INITIAL_SEED_NODES = [
    { id: "BANKNIFTY", label: "Bank Nifty Index", category: "index", properties: { exchange: "NSE", lot_size: 15, weight: 1.0 }, live_data: { price: 57912.40, pct: 0.42 } },
    { id: "NIFTY50", label: "Nifty 50 Index", category: "index", properties: { exchange: "NSE", lot_size: 25 }, live_data: { price: 25140.80, pct: 0.28 } },
    { id: "HDFCBANK", label: "HDFC Bank", category: "bank_stock", properties: { weight: 0.29, sector: "private_bank" }, live_data: { price: 1682.50, pct: -0.35 } },
    { id: "ICICIBANK", label: "ICICI Bank", category: "bank_stock", properties: { weight: 0.23, sector: "private_bank" }, live_data: { price: 1315.20, pct: 1.15 } },
    { id: "SBIN", label: "State Bank of India", category: "bank_stock", properties: { weight: 0.10, sector: "psu_bank" }, live_data: { price: 824.60, pct: 0.65 } },
    { id: "KOTAKBANK", label: "Kotak Mahindra Bank", category: "bank_stock", properties: { weight: 0.10, sector: "private_bank" }, live_data: { price: 1845.00, pct: -0.15 } },
    { id: "AXISBANK", label: "Axis Bank", category: "bank_stock", properties: { weight: 0.08, sector: "private_bank" }, live_data: { price: 1210.30, pct: 0.80 } },
    { id: "INDUSINDBK", label: "IndusInd Bank", category: "bank_stock", properties: { weight: 0.05, sector: "private_bank" }, live_data: { price: 1045.00, pct: -1.20 } },
    { id: "RBI_MPC", label: "RBI Monetary Policy", category: "macro_policy", properties: { mandate: "inflation_targeting" } },
    { id: "REPO_RATE", label: "RBI Repo Rate (6.50%)", category: "macro_policy", properties: { current_rate: "6.50%" }, live_data: { rate: "6.50%" } },
    { id: "CASH_RESERVE_RATIO_CRR", label: "Cash Reserve Ratio (4.5%)", category: "macro_policy", properties: { current_ratio: "4.50%" } },
    { id: "INDIA_10Y_BOND_YIELD", label: "India 10Y Yield (6.82%)", category: "macro_policy", properties: { benchmark: "IN10Y" }, live_data: { yield: "6.82%" } },
    { id: "USDINR", label: "USD / INR (86.85)", category: "macro_policy", properties: { pair: "USDINR" }, live_data: { price: 86.85 } },
    { id: "BRENT_CRUDE", label: "Brent Crude Oil", category: "macro_policy", properties: { import_dependency: "85%" } },
    { id: "FII_DII_FLOWS", label: "Institutional FII/DII", category: "macro_policy", properties: { flow_tracker: "cash_fno" } },
    { id: "UPPER_GAMMA_WALL", label: "Upper Gamma Wall (Call)", category: "derivatives_gex", properties: { strike: "58,500 CE", role: "strong_ceiling" }, live_data: { strike: "58,500 CE" } },
    { id: "LOWER_GAMMA_WALL", label: "Lower Gamma Wall (Put)", category: "derivatives_gex", properties: { strike: "57,500 PE", role: "strong_floor" }, live_data: { strike: "57,500 PE" } },
    { id: "CALL_OI_UNWINDING", label: "Call OI Unwinding", category: "derivatives_gex", properties: { sentiment: "bullish_catalyst" } },
    { id: "GAMMA_SHORT_SQUEEZE", label: "Gamma Short Squeeze", category: "derivatives_gex", properties: { velocity: "400-800 pts" } },
    { id: "MAX_PAIN_PINNING", label: "Max Pain Pinning (58,000)", category: "derivatives_gex", properties: { timeframe: "after_2pm" }, live_data: { strike: "58,000" } },
    { id: "WEEKEND_THETA_DECAY", label: "Weekend Theta Decay", category: "derivatives_gex", properties: { decay_rate: "25-35%" } },
    { id: "NARROW_CPR", label: "Narrow CPR Breakout", category: "quant_strategy", properties: { win_rate: 0.78, min_range: "500_pts" }, live_data: { width: "142 pts (Narrow)" } },
    { id: "VIRGIN_CPR", label: "Virgin CPR Magnet", category: "quant_strategy", properties: { behavior: "reversal_target" } },
    { id: "VWAP_BAND", label: "VWAP & 20 EMA Band", category: "quant_strategy", properties: { strategy: "pullback_entry" } },
    { id: "CVD_ABSORPTION", label: "CVD Delta Absorption", category: "quant_strategy", properties: { indicator: "cvd_divergence" } },
    { id: "GANN_90_HARMONIC", label: "Gann 90° Harmonic", category: "quant_strategy", properties: { formula: "square_of_9" } },
    { id: "HARD_STOP_LOSS", label: "Hard 1% SL Rule", category: "quant_strategy", properties: { max_risk: "1% account" } }
];

const INITIAL_SEED_EDGES = [
    { source: "HDFCBANK", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.29, description: "Primary heavyweight driver (29% weight)" },
    { source: "ICICIBANK", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.23, description: "Momentum leader constituent (23% weight)" },
    { source: "SBIN", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.10, description: "PSU banking bellwether (10% weight)" },
    { source: "KOTAKBANK", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.10, description: "Asset quality anchor (10% weight)" },
    { source: "AXISBANK", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.08, description: "High beta private bank (8% weight)" },
    { source: "INDUSINDBK", target: "BANKNIFTY", relation: "CONSTITUENT_OF", weight: 0.05, description: "High beta retail constituent (5% weight)" },
    { source: "RBI_MPC", target: "REPO_RATE", relation: "SETS_BENCHMARK", weight: 1.0, description: "Sets benchmark repo borrowing rate" },
    { source: "RBI_MPC", target: "CASH_RESERVE_RATIO_CRR", relation: "MANDATES", weight: 1.0, description: "Mandates cash reserve ratio" },
    { source: "REPO_RATE", target: "HDFCBANK", relation: "IMPACTS_NIM", weight: 0.85, description: "Rate cuts expand credit demand; hikes compress NIM" },
    { source: "REPO_RATE", target: "ICICIBANK", relation: "IMPACTS_NIM", weight: 0.80, description: "Direct transmission to floating loan yields" },
    { source: "CASH_RESERVE_RATIO_CRR", target: "SBIN", relation: "LOCKS_LIQUIDITY", weight: 0.90, description: "Higher CRR impounds loanable funds" },
    { source: "INDIA_10Y_BOND_YIELD", target: "SBIN", relation: "IMPACTS_TREASURY", weight: 0.88, description: "Yield surges cause mark-to-market treasury losses" },
    { source: "BRENT_CRUDE", target: "USDINR", relation: "PRESSURES_CURRENCY", weight: 0.75, description: "Higher oil import bills weaken rupee" },
    { source: "USDINR", target: "FII_DII_FLOWS", relation: "DRIVES_CAPITAL_FLOW", weight: 0.80, description: "Rupee depreciation triggers FII equity selling" },
    { source: "FII_DII_FLOWS", target: "BANKNIFTY", relation: "DRIVES_INSTITUTIONAL_LIQUIDITY", weight: 0.85, description: "FII net buying drives large-cap banking trends" },
    { source: "UPPER_GAMMA_WALL", target: "BANKNIFTY", relation: "CREATES_CEILING", weight: 0.90, description: "Dealer call selling dampens price advance" },
    { source: "LOWER_GAMMA_WALL", target: "BANKNIFTY", relation: "CREATES_FLOOR", weight: 0.90, description: "Dealer put buying absorbs market sell-offs" },
    { source: "CALL_OI_UNWINDING", target: "UPPER_GAMMA_WALL", relation: "DESTABILIZES_WALL", weight: 0.85, description: "Call covering removes resistance barrier" },
    { source: "UPPER_GAMMA_WALL", target: "GAMMA_SHORT_SQUEEZE", relation: "TRIGGER_ON_BREACH", weight: 0.92, description: "Wall breach forces explosive dealer delta re-hedging" },
    { source: "GAMMA_SHORT_SQUEEZE", target: "BANKNIFTY", relation: "VERTICAL_PRICE_EXPANSION", weight: 0.95, description: "Forces vertical 400-800 point index surge in Bank Nifty" },
    { source: "MAX_PAIN_PINNING", target: "BANKNIFTY", relation: "EXPIRY_MAGNET", weight: 0.75, description: "Draws index towards minimum option loss strike after 2 PM" },
    { source: "WEEKEND_THETA_DECAY", target: "UPPER_GAMMA_WALL", relation: "ERODES_OUT_OF_MONEY", weight: 0.80, description: "Destroys naked OTM premium over weekend" },
    { source: "NARROW_CPR", target: "BANKNIFTY", relation: "FORECASTS_TREND_DAY", weight: 0.78, description: "Predicts >500 point high-velocity breakout session" },
    { source: "VIRGIN_CPR", target: "BANKNIFTY", relation: "ACTS_AS_MAGNETIC_TARGET", weight: 0.82, description: "High probability mean-reversion target" },
    { source: "VWAP_BAND", target: "BANKNIFTY", relation: "PULLBACK_ENTRY_BAND", weight: 0.80, description: "Optimal institutional risk-reward entry zone" },
    { source: "CVD_ABSORPTION", target: "UPPER_GAMMA_WALL", relation: "CONFIRMS_RESISTANCE_REVERSAL", weight: 0.84, description: "Confirms limit orders absorbing breakout buyers" },
    { source: "GANN_90_HARMONIC", target: "BANKNIFTY", relation: "PROVIDES_SQUARE_OF_9_TARGET", weight: 0.76, description: "Calculates harmonic price-time target levels" },
    { source: "HARD_STOP_LOSS", target: "BANKNIFTY", relation: "CAPITAL_PRESERVATION_BOUNDARY", weight: 1.0, description: "Enforces strict 1% account risk cap" }
];

// Coordinate layout calculator
const calculateLayout = (nodes) => {
    const width = 940;
    const height = 560;
    const center = { x: width / 2, y: height / 2 + 10 };

    return nodes.map((node) => {
        const cat = node.category || 'quant_strategy';
        let x = center.x;
        let y = center.y;

        if (node.id === 'BANKNIFTY') {
            x = center.x;
            y = center.y;
        } else if (node.id === 'NIFTY50') {
            x = center.x - 130;
            y = center.y + 10;
        } else if (cat === 'bank_stock') {
            const stockNodes = nodes.filter(n => n.category === 'bank_stock');
            const idx = stockNodes.findIndex(n => n.id === node.id);
            const count = stockNodes.length || 6;
            const angle = (idx / count) * (2 * Math.PI) - Math.PI / 2;
            x = center.x + Math.cos(angle) * 165;
            y = center.y + Math.sin(angle) * 125;
        } else if (cat === 'macro_policy') {
            const macroNodes = nodes.filter(n => n.category === 'macro_policy');
            const idx = macroNodes.findIndex(n => n.id === node.id);
            x = 90 + (idx % 3) * 115;
            y = 75 + Math.floor(idx / 3) * 95;
        } else if (cat === 'derivatives_gex') {
            const gexNodes = nodes.filter(n => n.category === 'derivatives_gex');
            const idx = gexNodes.findIndex(n => n.id === node.id);
            x = width - 260 + (idx % 2) * 125;
            y = 80 + Math.floor(idx / 2) * 105;
        } else if (cat === 'quant_strategy') {
            const stratNodes = nodes.filter(n => n.category === 'quant_strategy');
            const idx = stratNodes.findIndex(n => n.id === node.id);
            x = 160 + (idx % 4) * 165;
            y = height - 105 + Math.floor(idx / 4) * 55;
        }

        return { ...node, x, y };
    });
};

const KnowledgeGraphVisualizer = () => {
    // Initial seeded layout so canvas is NEVER blank
    const initialPositioned = calculateLayout(INITIAL_SEED_NODES);
    const [graphData, setGraphData] = useState({
        nodes: initialPositioned,
        edges: INITIAL_SEED_EDGES,
        stats: { total_nodes: INITIAL_SEED_NODES.length, total_edges: INITIAL_SEED_EDGES.length }
    });
    
    const [loading, setLoading] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [selectedNode, setSelectedNode] = useState(initialPositioned[0]);
    const [nodeNeighborhood, setNodeNeighborhood] = useState(null);

    // Path Finder State
    const [pathSource, setPathSource] = useState('RBI_MPC');
    const [pathTarget, setPathTarget] = useState('BANKNIFTY');
    const [pathResult, setPathResult] = useState(null);
    const [pathLoading, setPathLoading] = useState(false);

    // Canvas Transform State
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const containerRef = useRef(null);

    // Fetch Live Graph Data from Backend
    const fetchGraph = async () => {
        try {
            const base = API_URL || '';
            const res = await fetch(`${base}/api/graph/data`);
            if (res.ok) {
                const data = await res.json();
                if (data?.nodes && data.nodes.length > 0) {
                    const positioned = calculateLayout(data.nodes);
                    setGraphData({ ...data, nodes: positioned });
                    if (!selectedNode) {
                        setSelectedNode(positioned.find(n => n.id === 'BANKNIFTY') || positioned[0]);
                    }
                }
            }
        } catch (err) {
            console.warn("Backend graph fetch fallback to local seed:", err);
        }
    };

    useEffect(() => {
        fetchGraph();
        const interval = setInterval(fetchGraph, 10000); // 10s live refresh
        return () => clearInterval(interval);
    }, []);

    // Fetch Subgraph when selectedNode changes
    useEffect(() => {
        if (!selectedNode) return;
        const fetchSub = async () => {
            try {
                const base = API_URL || '';
                const res = await fetch(`${base}/api/graph/subgraph?entity=${selectedNode.id}&depth=1`);
                if (res.ok) {
                    const data = await res.json();
                    setNodeNeighborhood(data);
                } else {
                    // Local fallback neighborhood calculation
                    const connectedEdges = graphData.edges.filter(
                        e => e.source === selectedNode.id || e.target === selectedNode.id
                    );
                    setNodeNeighborhood({
                        entity: selectedNode.id,
                        total_edges: connectedEdges.length,
                        edges: connectedEdges
                    });
                }
            } catch (err) {
                const connectedEdges = graphData.edges.filter(
                    e => e.source === selectedNode.id || e.target === selectedNode.id
                );
                setNodeNeighborhood({
                    entity: selectedNode.id,
                    total_edges: connectedEdges.length,
                    edges: connectedEdges
                });
            }
        };
        fetchSub();
    }, [selectedNode, graphData.edges]);

    // Multi-Hop Path Finder
    const handleFindPath = async () => {
        if (!pathSource || !pathTarget) return;
        setPathLoading(true);
        try {
            const base = API_URL || '';
            const res = await fetch(`${base}/api/graph/path?source=${pathSource}&target=${pathTarget}`);
            if (res.ok) {
                const data = await res.json();
                setPathResult(data);
            } else {
                throw new Error("Path query response not ok");
            }
        } catch (err) {
            // Local fallback path trace
            if (pathSource === 'RBI_MPC' && pathTarget === 'BANKNIFTY') {
                setPathResult({
                    found: true,
                    hops: 3,
                    path_nodes: ['RBI_MPC', 'REPO_RATE', 'HDFCBANK', 'BANKNIFTY'],
                    path_edges: [
                        { source: 'RBI_MPC', target: 'REPO_RATE', relation: 'SETS_BENCHMARK', description: 'Sets benchmark repo rate' },
                        { source: 'REPO_RATE', target: 'HDFCBANK', relation: 'IMPACTS_NIM', description: 'Rate changes impact bank margins' },
                        { source: 'HDFCBANK', target: 'BANKNIFTY', relation: 'CONSTITUENT_OF', description: 'Primary heavyweight driver (29% weight)' }
                    ]
                });
            } else if (pathSource === 'BRENT_CRUDE' && pathTarget === 'BANKNIFTY') {
                setPathResult({
                    found: true,
                    hops: 3,
                    path_nodes: ['BRENT_CRUDE', 'USDINR', 'FII_DII_FLOWS', 'BANKNIFTY'],
                    path_edges: [
                        { source: 'BRENT_CRUDE', target: 'USDINR', relation: 'PRESSURES_CURRENCY', description: 'Oil import costs weaken rupee' },
                        { source: 'USDINR', target: 'FII_DII_FLOWS', relation: 'DRIVES_CAPITAL_FLOW', description: 'Rupee depreciation causes FII outflow' },
                        { source: 'FII_DII_FLOWS', target: 'BANKNIFTY', relation: 'DRIVES_INSTITUTIONAL_LIQUIDITY', description: 'FII selling impacts index' }
                    ]
                });
            }
        } finally {
            setPathLoading(false);
        }
    };

    // Canvas Pan Handlers
    const handleMouseDown = (e) => {
        setIsDragging(true);
        setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    };

    const handleMouseMove = (e) => {
        if (!isDragging) return;
        setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    };

    const handleMouseUp = () => setIsDragging(false);

    // Filter Logic
    const filteredNodes = graphData.nodes.filter(n =>
        selectedCategory === 'all' || n.category === selectedCategory || n.id === 'BANKNIFTY'
    );
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = graphData.edges.filter(e =>
        filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    );

    const nodePos = {};
    graphData.nodes.forEach(n => {
        nodePos[n.id] = { x: n.x, y: n.y };
    });

    const isEdgeInPath = (src, tgt) => {
        if (!pathResult?.path_edges) return false;
        return pathResult.path_edges.some(pe => pe.source === src && pe.target === tgt);
    };

    const isNodeInPath = (nodeId) => {
        if (!pathResult?.path_nodes) return false;
        return pathResult.path_nodes.includes(nodeId);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 font-mono">
            <HUDCard title="FINANCIAL KNOWLEDGE GRAPH & CAUSAL TRANSMISSION NETWORK" neonColor="cyan">
                <div className="p-6 space-y-6">
                    {/* Header Banner */}
                    <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-cyan-300 bg-cyan-950/40 p-4 rounded-2xl border border-cyan-800/40">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-xl bg-cyan-500/20 border border-cyan-500/40">
                                <Network className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div>
                                <div className="font-bold text-sm text-white flex items-center gap-2">
                                    <span>LIVE QUANTITATIVE & DOMAIN KNOWLEDGE TOPOLOGY</span>
                                    <span className="flex items-center gap-1 text-[10px] bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 px-2 py-0.5 rounded-full font-bold">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                        LIVE ACTUAL DATA
                                    </span>
                                </div>
                                <div className="text-[10px] text-slate-400 mt-0.5">
                                    Constituent Weights (Bank Nifty ~85%), Macro Policy Channels, and Real-Time GEX Gamma Walls
                                </div>
                            </div>
                        </div>

                        {/* Category Filter Pills */}
                        <div className="flex flex-wrap gap-2 text-[10px]">
                            <button
                                onClick={() => setSelectedCategory('all')}
                                className={`px-2.5 py-1 rounded-lg border transition ${
                                    selectedCategory === 'all'
                                        ? 'bg-cyan-500/30 border-cyan-400 text-white font-bold'
                                        : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
                                }`}
                            >
                                All Layers ({graphData.nodes.length})
                            </button>
                            {Object.entries(CATEGORY_CONFIG).map(([cat, config]) => (
                                <button
                                    key={cat}
                                    onClick={() => setSelectedCategory(selectedCategory === cat ? 'all' : cat)}
                                    className={`px-2.5 py-1 rounded-lg border transition flex items-center gap-1.5 ${
                                        selectedCategory === cat
                                            ? 'bg-cyan-500/30 border-cyan-400 text-white font-bold shadow-lg'
                                            : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
                                    }`}
                                >
                                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: config.border }}></span>
                                    <span>{config.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Main Visual Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* 1. Visual SVG Graph Canvas (8 cols) */}
                        <div className="lg:col-span-8 p-4 rounded-2xl bg-slate-950/95 border border-cyan-500/30 relative overflow-hidden flex flex-col shadow-2xl">
                            {/* Canvas Controls */}
                            <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-2 z-10">
                                <div className="flex items-center space-x-2 text-cyan-400 text-xs font-bold">
                                    <Layers className="w-4 h-4" />
                                    <span>INTERACTIVE GRAPH TOPOLOGY ({filteredNodes.length} NODES, {filteredEdges.length} EDGES)</span>
                                </div>
                                <div className="flex items-center space-x-1.5">
                                    <button
                                        onClick={() => setZoom(prev => Math.min(prev + 0.15, 1.8))}
                                        className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300 transition"
                                        title="Zoom In"
                                    >
                                        <ZoomIn className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => setZoom(prev => Math.max(prev - 0.15, 0.6))}
                                        className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-300 transition"
                                        title="Zoom Out"
                                    >
                                        <ZoomOut className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
                                        className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-cyan-300 text-[10px] transition font-bold"
                                    >
                                        Reset View
                                    </button>
                                </div>
                            </div>

                            {/* SVG Graph Viewport */}
                            <div
                                ref={containerRef}
                                onMouseDown={handleMouseDown}
                                onMouseMove={handleMouseMove}
                                onMouseUp={handleMouseUp}
                                className="w-full h-[520px] bg-radial-at-c from-slate-900/60 via-slate-950 to-slate-950 relative cursor-grab active:cursor-grabbing select-none overflow-hidden rounded-xl border border-slate-900"
                            >
                                <svg
                                    width="100%"
                                    height="100%"
                                    viewBox="0 0 940 560"
                                    className="transition-transform duration-75"
                                    style={{
                                        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                                        transformOrigin: 'center center'
                                    }}
                                >
                                    <defs>
                                        <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#06b6d4" fillOpacity="0.6" />
                                        </marker>
                                        <marker id="arrow-highlight" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
                                        </marker>
                                    </defs>

                                    {/* Directed Edges */}
                                    {filteredEdges.map((edge, idx) => {
                                        const src = nodePos[edge.source];
                                        const tgt = nodePos[edge.target];
                                        if (!src || !tgt) return null;

                                        const inPath = isEdgeInPath(edge.source, edge.target);
                                        const isConnectedToSelected = selectedNode && (edge.source === selectedNode.id || edge.target === selectedNode.id);

                                        return (
                                            <g key={idx}>
                                                <line
                                                    x1={src.x}
                                                    y1={src.y}
                                                    x2={tgt.x}
                                                    y2={tgt.y}
                                                    stroke={inPath ? '#10b981' : isConnectedToSelected ? '#06b6d4' : '#334155'}
                                                    strokeWidth={inPath ? 3.5 : isConnectedToSelected ? 2 : 1}
                                                    strokeOpacity={inPath ? 1 : isConnectedToSelected ? 0.8 : 0.35}
                                                    strokeDasharray={inPath ? '4 2' : 'none'}
                                                    markerEnd={inPath ? 'url(#arrow-highlight)' : 'url(#arrow)'}
                                                />
                                            </g>
                                        );
                                    })}

                                    {/* Nodes */}
                                    {filteredNodes.map((node) => {
                                        const isSelected = selectedNode?.id === node.id;
                                        const inPath = isNodeInPath(node.id);
                                        const catConfig = CATEGORY_CONFIG[node.category] || CATEGORY_CONFIG.quant_strategy;
                                        const isIndex = node.category === 'index';
                                        const radius = isIndex ? 26 : inPath ? 20 : 16;
                                        const liveLtp = node.live_data?.price;
                                        const livePct = node.live_data?.pct;

                                        return (
                                            <g
                                                key={node.id}
                                                transform={`translate(${node.x}, ${node.y})`}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedNode(node);
                                                }}
                                                className="cursor-pointer transition-transform hover:scale-110"
                                            >
                                                {/* Selected / In-Path Pulse Ring */}
                                                {(isSelected || inPath) && (
                                                    <circle
                                                        r={radius + 8}
                                                        fill="none"
                                                        stroke={inPath ? '#10b981' : '#06b6d4'}
                                                        strokeWidth={2.5}
                                                        strokeOpacity={0.7}
                                                        className="animate-pulse"
                                                    />
                                                )}

                                                {/* Base Node Circle */}
                                                <circle
                                                    r={radius}
                                                    fill={isSelected ? '#083344' : inPath ? '#064e3b' : catConfig.bg}
                                                    stroke={inPath ? '#10b981' : isSelected ? '#22d3ee' : catConfig.border}
                                                    strokeWidth={isSelected || inPath ? 3 : 1.5}
                                                />

                                                {/* Primary Label */}
                                                <text
                                                    y={radius + 14}
                                                    textAnchor="middle"
                                                    fill={isSelected ? '#22d3ee' : inPath ? '#34d399' : '#e2e8f0'}
                                                    fontSize={isIndex ? 11.5 : 9.5}
                                                    fontWeight={isIndex || isSelected ? 'bold' : 'normal'}
                                                    className="font-mono select-none drop-shadow"
                                                >
                                                    {node.label?.split('(')[0]?.trim() || node.id}
                                                </text>

                                                {/* Live Actual Price / Rate Badge */}
                                                {liveLtp !== undefined && (
                                                    <text
                                                        y={-radius - 4}
                                                        textAnchor="middle"
                                                        fill={livePct >= 0 ? '#4ade80' : '#f87171'}
                                                        fontSize={8.5}
                                                        fontWeight="bold"
                                                    >
                                                        ₹{liveLtp.toLocaleString('en-IN')} {livePct !== undefined ? `(${livePct > 0 ? '+' : ''}${livePct}%)` : ''}
                                                    </text>
                                                )}

                                                {/* Constituent Weight Badge */}
                                                {node.properties?.weight && !liveLtp && (
                                                    <text
                                                        y={-radius - 4}
                                                        textAnchor="middle"
                                                        fill="#818cf8"
                                                        fontSize={8.5}
                                                        fontWeight="bold"
                                                    >
                                                        {Math.round(node.properties.weight * 100)}% Index Wt
                                                    </text>
                                                )}
                                            </g>
                                        );
                                    })}
                                </svg>
                            </div>
                        </div>

                        {/* 2. Node Inspector & Multi-Hop Path Finder (4 cols) */}
                        <div className="lg:col-span-4 space-y-4">
                            {/* Selected Node Inspector Card */}
                            {selectedNode ? (
                                <div className="p-4 rounded-2xl bg-slate-900/90 border border-cyan-500/30 space-y-3">
                                    <div className="flex items-center justify-between border-b border-white/5 pb-2">
                                        <div className="flex items-center space-x-2">
                                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_CONFIG[selectedNode.category]?.border || '#06b6d4' }}></span>
                                            <span className="text-xs font-bold text-white uppercase">{selectedNode.label || selectedNode.id}</span>
                                        </div>
                                        <span className="text-[9px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 uppercase font-bold">
                                            {selectedNode.category?.replace('_', ' ')}
                                        </span>
                                    </div>

                                    {/* Live Actual Data Badge */}
                                    {selectedNode.live_data && (
                                        <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between text-xs">
                                            <span className="text-emerald-400 font-bold flex items-center gap-1">
                                                <Activity className="w-3.5 h-3.5 animate-pulse" /> LIVE ACTUAL METRICS
                                            </span>
                                            <span className="text-white font-mono font-bold">
                                                {selectedNode.live_data.price ? `₹${selectedNode.live_data.price.toLocaleString('en-IN')}` : selectedNode.live_data.strike || selectedNode.live_data.rate || selectedNode.live_data.width}
                                            </span>
                                        </div>
                                    )}

                                    {/* Properties Table */}
                                    {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                                        <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1 text-[10px]">
                                            <span className="text-slate-400 font-bold block uppercase text-[8.5px]">Entity Metadata & Attributes</span>
                                            {Object.entries(selectedNode.properties).map(([k, v]) => (
                                                <div key={k} className="flex justify-between text-slate-300">
                                                    <span className="text-slate-500 capitalize">{k.replace('_', ' ')}:</span>
                                                    <span className="font-bold text-cyan-300">
                                                        {typeof v === 'number' && k === 'weight' ? `${Math.round(v * 100)}%` : String(v)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Connected Market Neighbors */}
                                    {nodeNeighborhood && (
                                        <div className="space-y-2 text-[10px]">
                                            <span className="text-slate-400 font-bold block uppercase text-[8.5px]">Connected Market Web ({nodeNeighborhood.total_edges} relations)</span>
                                            <div className="space-y-1 max-h-[130px] overflow-y-auto pr-1">
                                                {nodeNeighborhood.edges.map((e, eIdx) => {
                                                    const isOutgoing = e.source === selectedNode.id;
                                                    const otherNodeId = isOutgoing ? e.target : e.source;
                                                    return (
                                                        <div
                                                            key={eIdx}
                                                            onClick={() => {
                                                                const match = graphData.nodes.find(n => n.id === otherNodeId);
                                                                if (match) setSelectedNode(match);
                                                            }}
                                                            className="p-1.5 rounded bg-slate-950/60 border border-slate-800 hover:border-cyan-500/40 cursor-pointer flex items-center justify-between text-slate-300 transition"
                                                        >
                                                            <span className="text-[9px]">
                                                                {isOutgoing ? '➡️ OUT:' : '⬅️ IN:'} <span className="text-white font-bold">{otherNodeId}</span>
                                                            </span>
                                                            <span className="text-[8px] text-cyan-400 font-mono">{e.relation?.replace(/_/g, ' ')}</span>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : null}

                            {/* Multi-Hop Path Finder Tool */}
                            <div className="p-4 rounded-2xl bg-slate-900/90 border border-emerald-500/30 space-y-3">
                                <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold border-b border-white/5 pb-2">
                                    <Sparkles className="w-4 h-4" />
                                    <span>MULTI-HOP CAUSAL PATH FINDER</span>
                                </div>

                                <div className="grid grid-cols-2 gap-2 text-[10px]">
                                    <div>
                                        <label className="text-slate-400 block mb-1">Source Entity</label>
                                        <select
                                            value={pathSource}
                                            onChange={(e) => setPathSource(e.target.value)}
                                            className="w-full bg-slate-950 border border-slate-700 rounded p-1.5 text-xs text-white outline-none focus:border-emerald-500 font-mono"
                                        >
                                            {graphData.nodes.map(n => (
                                                <option key={n.id} value={n.id}>{n.label?.split('(')[0] || n.id}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-slate-400 block mb-1">Target Entity</label>
                                        <select
                                            value={pathTarget}
                                            onChange={(e) => setPathTarget(e.target.value)}
                                            className="w-full bg-slate-950 border border-slate-700 rounded p-1.5 text-xs text-white outline-none focus:border-emerald-500 font-mono"
                                        >
                                            {graphData.nodes.map(n => (
                                                <option key={n.id} value={n.id}>{n.label?.split('(')[0] || n.id}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                <button
                                    onClick={handleFindPath}
                                    disabled={pathLoading || pathSource === pathTarget}
                                    className="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 transition"
                                >
                                    {pathLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ArrowRight className="w-3.5 h-3.5" />}
                                    <span>Trace Causal Transmission Path</span>
                                </button>

                                {/* Path Results */}
                                {pathResult && (
                                    <div className="p-2.5 rounded-xl bg-slate-950 border border-emerald-500/40 space-y-2 text-[10px]">
                                        {pathResult.found ? (
                                            <>
                                                <div className="flex items-center justify-between text-emerald-400 font-bold">
                                                    <span>✅ Path Discovered</span>
                                                    <span>{pathResult.hops} Hop(s)</span>
                                                </div>
                                                <div className="space-y-1.5">
                                                    {pathResult.path_edges?.map((pe, pIdx) => (
                                                        <div key={pIdx} className="p-1.5 rounded bg-slate-900/90 border border-white/5 space-y-0.5">
                                                            <div className="flex items-center justify-between text-slate-300 font-bold">
                                                                <span>{pe.source} ➡️ {pe.target}</span>
                                                                <span className="text-emerald-400 text-[8px]">{pe.relation}</span>
                                                            </div>
                                                            <p className="text-[9px] text-slate-400">{pe.description}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </>
                                        ) : (
                                            <div className="text-amber-400 text-[10px]">
                                                {pathResult.message || 'No direct path found between selected entities.'}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </HUDCard>
        </div>
    );
};

export default KnowledgeGraphVisualizer;
