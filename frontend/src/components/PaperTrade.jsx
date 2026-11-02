import React, { useState, useEffect } from 'react';
import {
    Send, RefreshCw, TrendingUp, TrendingDown,
    XCircle, Clock, CheckCircle, AlertTriangle, Zap, Bot
} from 'lucide-react';
import { workerSetInterval, workerClearInterval } from '../utils/workerTimer';
import { getApiUrl, API_URL } from '../config/api';


const PaperTrade = ({ token, symbol, ltp }) => {
    const [action, setAction] = useState('BUY');
    const [quantity, setQuantity] = useState(15);
    const [reasoning, setReasoning] = useState('');
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState(null);
    const [isAuto, setIsAuto] = useState(true);
    const [isTurbo, setIsTurbo] = useState(true);
    const [autoLogs, setAutoLogs] = useState([]);

    const showToast = (msg, type = 'info') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchPositions = async () => {
        try {
            const res = await fetch(`${API_URL}/api/paper/positions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setPositions(data);
        } catch (e) {
            console.error("Failed to fetch positions", e);
        }
    };

    useEffect(() => {
        if (token) fetchPositions();
        const interval = workerSetInterval(fetchPositions, 5000);
        return () => workerClearInterval(interval);
    }, [token]);

    // Auto-Trading Logic
    useEffect(() => {
        let autoInterval;
        if (isAuto) {
            const runAutoCycle = async () => {
                try {
                    const res = await fetch(`${API_URL}/api/trading/autopilot`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            symbol,
                            quantity: 1,
                            mode: 'PAPER',
                            greedy: isTurbo
                        })
                    });
                    const result = await res.json();

                    if (result.status === 'EXECUTED') {
                        showToast(`Auto-Trade: ${result.signal} Executed!`, 'success');
                        fetchPositions();
                        setAutoLogs(prev => [`[${new Date().toLocaleTimeString()}] EXECUTED: ${result.signal} @ ${ltp}`, ...prev.slice(0, 4)]);
                    } else if (result.status === 'HOLD') {
                        // Optional: Log holds
                        setAutoLogs(prev => [`[${new Date().toLocaleTimeString()}] SCANNED: HOLD (Signal Weak)`, ...prev.slice(0, 4)]);
                    }
                } catch (e) {
                    console.error("Auto-Trade Failed", e);
                }
            };

            runAutoCycle(); // Immediate run
            autoInterval = workerSetInterval(runAutoCycle, 5000); // Run every 5 seconds (Turbo Simulation)
        }
        return () => workerClearInterval(autoInterval);
    }, [isAuto, symbol, token, ltp]);

    const handleTrade = async () => {
        if (!reasoning.trim()) {
            showToast("Please enter a reason for this trade.", "error");
            return;
        }
        setLoading(true);
        try {
            const payload = {
                symbol,
                side: action,
                quantity: parseInt(quantity),
                price: ltp,
                type: 'MARKET',
                reasoning: reasoning,
                mode: 'MANUAL'
            };

            const res = await fetch(`${API_URL}/api/paper/trade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const result = await res.json();
            if (result.status === 'success') {
                showToast("Paper Trade Executed!", "success");
                setReasoning(''); // Reset
                fetchPositions();
            } else {
                showToast("Trade Failed", "error");
            }
        } catch (e) {
            showToast("Server Error", "error");
        }
        setLoading(false);
    };

    const closePosition = async (trade_id) => {
        if (!window.confirm("Close this paper position?")) return;
        try {
            const res = await fetch(`${API_URL}/api/paper/close`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    trade_id: trade_id,
                    exit_price: ltp,
                    reasoning: "Manual Close via UI"
                })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast("Position Closed", "success");
                fetchPositions();
            }
        } catch (e) {
            showToast("Failed to close position", "error");
        }
    };

    const [simResult, setSimResult] = useState(null);
    const [simLoading, setSimLoading] = useState(false);

    const runGannAstroSimulation = async () => {
        setSimLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/run_prediction_simulation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    symbol: symbol || "BANKNIFTY",
                    technique: "Gann Sq9 + Financial Astrology + VWAP + RSI(14) 54/46 Confluence"
                })
            });
            const data = await res.json();
            if (data.status === 'SUCCESS') {
                setSimResult(data.prediction);
                showToast(`🚀 Prediction Simulation Executed & Logged to Observatory!`, 'success');
                setAutoLogs(prev => [`[${new Date().toLocaleTimeString()}] OBSERVATORY RECORD: ${data.prediction.prediction.signal} @ ${data.prediction.prediction.strike}`, ...prev.slice(0, 4)]);
            } else {
                showToast("Simulation execution failed", "error");
            }
        } catch (e) {
            showToast("Server connection error", "error");
        }
        setSimLoading(false);
    };

    return (
        <div className="space-y-6">
            {toast && (
                <div className={`fixed top-4 right-4 px-4 py-2 rounded-lg text-white shadow-lg z-50 ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'}`}>
                    {toast.msg}
                </div>
            )}

            {/* GANN + ASTRO CONFLUENCE SIMULATION RUNNER BANNER */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/80 to-purple-950/80 border border-indigo-500/40 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                        <Zap className="w-6 h-6 animate-pulse" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-black uppercase text-cyan-300 tracking-wider">
                                GANN + ASTRO + VWAP + RSI 54 PREDICTION SIMULATION ENGINE
                            </span>
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                                PIPED TO OBSERVATORY
                            </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-0.5">
                            Simulate active trades for <strong>{symbol || 'BANKNIFTY'}</strong> using high-conviction confluence rules. Results automatically stream to <strong>Observatory</strong> for multi-day pattern & win-rate analysis.
                        </p>
                    </div>
                </div>

                <button
                    onClick={runGannAstroSimulation}
                    disabled={simLoading}
                    className="w-full md:w-auto px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-black text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/30 transition-all transform active:scale-95 flex items-center justify-center gap-2 whitespace-nowrap"
                >
                    <Bot className={`w-4 h-4 ${simLoading ? 'animate-spin' : ''}`} />
                    <span>{simLoading ? 'RUNNING SIMULATION...' : '🚀 RUN PREDICTION SIMULATION'}</span>
                </button>
            </div>

            {/* LIVE SIMULATION RESULT CALLOUT */}
            {simResult && (
                <div className="p-4 rounded-2xl bg-slate-900 border border-emerald-500/40 font-mono text-xs space-y-2 animate-in fade-in duration-300">
                    <div className="flex justify-between items-center border-b border-emerald-500/30 pb-2">
                        <span className="font-black text-emerald-400 flex items-center gap-1.5">
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            SIMULATION EXECUTED & STORED IN OBSERVATORY // {simResult.symbol}
                        </span>
                        <span className="text-[10px] text-slate-400">{simResult.timestamp}</span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px]">
                        <div className="p-2 rounded bg-black/60 border border-slate-800">
                            <span className="text-slate-400 block text-[9px]">RECOMMENDED STRIKE</span>
                            <span className="text-white font-black">{simResult.prediction.strike}</span>
                        </div>
                        <div className="p-2 rounded bg-black/60 border border-slate-800">
                            <span className="text-slate-400 block text-[9px]">CONFLUENCE SCORE</span>
                            <span className="text-emerald-300 font-black">{simResult.prediction.confidence * 100}% (HIGH)</span>
                        </div>
                        <div className="p-2 rounded bg-black/60 border border-slate-800">
                            <span className="text-slate-400 block text-[9px]">MARKET CONTEXT</span>
                            <span className="text-cyan-300 font-bold">RSI: {simResult.market_context.rsi_14} | {simResult.market_context.gann_angle}</span>
                        </div>
                        <div className="p-2 rounded bg-black/60 border border-slate-800">
                            <span className="text-slate-400 block text-[9px]">OBSERVATORY PnL</span>
                            <span className={`font-black ${simResult.actual_outcome.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                ₹{simResult.actual_outcome.pnl} ({simResult.actual_outcome.pnl_pct}%)
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Trading Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-900/50 backdrop-blur-sm p-6 rounded-2xl border border-indigo-500/20 shadow-xl">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
                                <Send className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white">New Simulation Order</h3>
                                <div className="text-xs font-mono text-slate-400">LTP: <span className="text-white">{ltp}</span></div>
                            </div>
                        </div>

                        {/* Auto-Simulation Toggle */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setIsTurbo(!isTurbo)}
                                className={`flex items-center gap-2 px-3 py-2 rounded-xl border transition-all ${isTurbo
                                    ? 'bg-amber-600 border-amber-500 text-white shadow-[0_0_15px_rgba(245,158,11,0.3)]'
                                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                                title="Enables Greedy Simulation (Lower signal threshold for more frequent trades)"
                            >
                                <Zap className={`w-3.5 h-3.5 ${isTurbo ? 'fill-current' : ''}`} />
                                <span className="text-[10px] font-black uppercase tracking-widest">{isTurbo ? 'TURBO ON' : 'TURBO OFF'}</span>
                            </button>

                            <button
                                onClick={() => setIsAuto(!isAuto)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-all ${isAuto
                                    ? 'bg-indigo-600 border-indigo-500 text-white shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'}`}
                            >
                                <Bot className={`w-4 h-4 ${isAuto ? 'animate-pulse' : ''}`} />
                                <span className="text-xs font-black uppercase tracking-widest">{isAuto ? 'AUTO ON' : 'AUTO OFF'}</span>
                            </button>
                        </div>
                    </div>

                    {isAuto && (
                        <div className="mb-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-3">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <Zap className="w-3 h-3 text-indigo-400" />
                                    <span className="text-[10px] font-black uppercase text-indigo-300">Live Simulation Log</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                    <span className="text-[8px] font-black text-emerald-400 uppercase tracking-tighter">Live Market Active</span>
                                </div>
                            </div>
                            <div className="space-y-1">
                                {autoLogs.map((log, i) => (
                                    <div key={i} className="text-[9px] font-mono text-slate-400 truncate border-b border-indigo-500/10 last:border-0 pb-1 last:pb-0">
                                        {log}
                                    </div>
                                ))}
                                {autoLogs.length === 0 && <div className="text-[9px] text-slate-600 italic">Initializing scanner...</div>}
                            </div>
                        </div>
                    )}

                    {!isAuto && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                            <div className="flex bg-slate-800 rounded-xl p-1">
                                {['BUY', 'SELL'].map(s => (
                                    <button
                                        key={s}
                                        onClick={() => setAction(s)}
                                        className={`flex-1 py-2 rounded-lg font-bold text-sm transition-all ${action === s
                                            ? (s === 'BUY' ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' : 'bg-red-500 text-white shadow-lg shadow-red-500/20')
                                            : 'text-slate-400 hover:text-white'
                                            }`}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-slate-500 uppercase font-bold ml-1">Symbol</label>
                                    <input
                                        type="text"
                                        value={symbol}
                                        readOnly
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 uppercase font-bold ml-1">Quantity</label>
                                    <input
                                        type="number"
                                        value={quantity}
                                        onChange={(e) => setQuantity(e.target.value)}
                                        className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white font-mono"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs text-slate-500 uppercase font-bold ml-1">Trade Rationale (Required)</label>
                                <textarea
                                    value={reasoning}
                                    onChange={(e) => setReasoning(e.target.value)}
                                    placeholder="Why are you taking this trade? (e.g. Breakout retest, Delta Divergence...)"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white h-24 focus:outline-none focus:border-indigo-500/50"
                                />
                            </div>

                            <button
                                onClick={handleTrade}
                                disabled={loading}
                                className={`w-full py-4 rounded-xl font-bold text-white shadow-lg transition-transform active:scale-95 ${action === 'BUY'
                                    ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 shadow-emerald-500/20'
                                    : 'bg-gradient-to-r from-red-500 to-red-600 shadow-red-500/20'
                                    }`}
                            >
                                {loading ? 'Executing...' : `PLACE ${action} ORDER`}
                            </button>
                        </div>
                    )}
                </div>

                {/* Open Positions Panel */}
                <div className="bg-slate-900/50 backdrop-blur-sm p-6 rounded-2xl border border-indigo-500/20 shadow-xl overflow-hidden">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
                            <Clock className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-bold text-white">Open Positions</h3>
                    </div>

                    <div className="h-[320px] overflow-y-auto space-y-3">
                        {positions.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                <CheckCircle className="w-8 h-8 mb-2 opacity-50" />
                                <p className="text-sm">No Open Positions</p>
                            </div>
                        ) : (
                            positions.map(pos => {
                                const currentVal = ltp * pos.quantity;
                                const entryVal = pos.entry_price * pos.quantity;
                                const pnl = pos.side === 'BUY' ? (currentVal - entryVal) : (entryVal - currentVal);
                                const isProfit = pnl >= 0;

                                return (
                                    <div key={pos.trade_id} className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50 flex flex-col gap-2">
                                        <div className="flex justify-between items-start">
                                            <div className="flex gap-2 items-center">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${pos.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                                                    }`}>
                                                    {pos.side}
                                                </span>
                                                <span className="font-bold text-sm tracking-wide">{pos.symbol}</span>
                                            </div>
                                            <span className={`font-mono font-bold ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {isProfit ? '+' : ''}{pnl.toFixed(2)}
                                            </span>
                                        </div>

                                        <div className="flex justify-between items-center text-xs text-slate-400">
                                            <span>Qty: {pos.quantity} @ {pos.entry_price}</span>
                                            <span className="font-mono text-white">LTP: {ltp}</span>
                                        </div>

                                        <div className="mt-2 text-[10px] text-slate-500 italic truncate border-t border-slate-700/50 pt-2">
                                            "{pos.reasoning}"
                                        </div>

                                        <button
                                            onClick={() => closePosition(pos.trade_id)}
                                            className="mt-2 w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-bold text-white transition-colors"
                                        >
                                            CLOSE POSITION
                                        </button>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaperTrade;
