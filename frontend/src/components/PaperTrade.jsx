import React, { useState, useEffect } from 'react';
import {
    Send, RefreshCw, TrendingUp, TrendingDown,
    XCircle, Clock, CheckCircle, AlertTriangle, Zap, Bot
} from 'lucide-react';
import { workerSetInterval, workerClearInterval } from '../utils/workerTimer';

const getApiUrl = () => {
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved) return saved.replace(/\/$/, '');
    } catch (e) { }
    return import.meta.env.VITE_API_URL || "";
};
const API_URL = getApiUrl();

const GITHUB_RAW_SUMMARY_URL = 'https://raw.githubusercontent.com/GhilliHari/tradeverse/main/backend/observatory_data/latest_summary.json';

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
    const [syncing, setSyncing] = useState(false);
    const [githubStatus, setGithubStatus] = useState({
        repo: 'GhilliHari/tradeverse',
        latest_commit: 'main',
        source: 'GitHub Sync'
    });
    const [summary, setSummary] = useState({
        date: '',
        open_count: 0,
        closed_today_count: 0,
        wins: 0,
        losses: 0,
        win_rate: 0,
        total_pnl: 0,
        recent_closed: [],
        all_time_closed: 0,
        all_time_pnl: 0
    });

    const showToast = (msg, type = 'info') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const applyPaperSummary = (sumData) => {
        if (!sumData) return;
        setSummary(sumData);
        if (sumData.recent_closed && sumData.recent_closed.length > 0) {
            const recentFormatted = sumData.recent_closed.slice(0, 6).map(t => {
                const ts = (t.timestamp || '').slice(11, 19) || '15:25:00';
                const pnlStr = t.pnl >= 0 ? `+₹${Number(t.pnl).toFixed(0)}` : `-₹${Math.abs(Number(t.pnl)).toFixed(0)}`;
                return `[${ts}] ${t.symbol}: ₹${t.entry_price} → ₹${t.exit_price} (${pnlStr})`;
            });
            setAutoLogs(prev => prev.length > 0 ? prev : recentFormatted);
        }
    };

    const fetchFromGitHubFallback = async () => {
        try {
            const res = await fetch(`${GITHUB_RAW_SUMMARY_URL}?t=${Date.now()}`);
            if (res.ok) {
                const data = await res.json();
                if (data.paper_summary) {
                    applyPaperSummary(data.paper_summary);
                }
                setGithubStatus({
                    repo: data.repo || 'GhilliHari/tradeverse',
                    latest_commit: 'GitHub Cloud',
                    source: 'GitHub Cloud Fallback'
                });
            }
        } catch (err) {
            console.error("GitHub fallback fetch failed", err);
        }
    };

    const fetchPositions = async () => {
        try {
            const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
            const [posRes, sumRes, ghRes] = await Promise.all([
                fetch(`${API_URL}/api/paper/positions`, { headers }),
                fetch(`${API_URL}/api/paper/summary`, { headers }),
                fetch(`${API_URL}/api/github/status`, { headers }).catch(() => null)
            ]);
            if (posRes.ok) {
                const posData = await posRes.json();
                setPositions(Array.isArray(posData) ? posData : []);
            }
            if (sumRes.ok) {
                const sumData = await sumRes.json();
                applyPaperSummary(sumData);
            } else {
                await fetchFromGitHubFallback();
            }
            if (ghRes && ghRes.ok) {
                const ghData = await ghRes.json();
                setGithubStatus({
                    repo: ghData.repo || 'GhilliHari/tradeverse',
                    latest_commit: ghData.latest_commit || 'main',
                    source: ghData.is_synced ? 'GitHub Synced' : 'GitHub Active'
                });
            }
        } catch (e) {
            await fetchFromGitHubFallback();
        }
    };

    const handleSyncMarketHours = async () => {
        setSyncing(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/backfill?days=14&push_github=true`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (res.ok) {
                const data = await res.json();
                const ghCommit = data.github_backup?.commit_hash ? ` • GitHub #${data.github_backup.commit_hash}` : '';
                showToast(`Synced & Backed up to GitHub${ghCommit}`, 'success');
                await fetchPositions();
            } else {
                await fetchFromGitHubFallback();
                showToast('Loaded backup directly from GitHub!', 'info');
            }
        } catch (e) {
            await fetchFromGitHubFallback();
            showToast('Loaded backup directly from GitHub!', 'info');
        }
        setSyncing(false);
    };

    useEffect(() => {
        fetchPositions();
        const interval = workerSetInterval(fetchPositions, 5000);
        return () => workerClearInterval(interval);
    }, [token]);

    // Auto-Trading Logic during Market Hours (09:15 - 15:30 IST)
    useEffect(() => {
        let autoInterval;
        if (isAuto) {
            const isMarketOpenNow = () => {
                const now = new Date();
                const day = now.getDay();
                if (day === 0 || day === 6) return false;
                const mins = now.getHours() * 60 + now.getMinutes();
                return mins >= (9 * 60 + 15) && mins <= (15 * 60 + 30);
            };

            const runAutoCycle = async () => {
                if (!isMarketOpenNow()) return;
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
                        setAutoLogs(prev => [`[${new Date().toLocaleTimeString()}] EXECUTED: ${result.signal} @ ${ltp}`, ...prev.slice(0, 5)]);
                    } else if (result.status === 'HOLD') {
                        setAutoLogs(prev => [`[${new Date().toLocaleTimeString()}] SCANNED: HOLD (Signal Weak)`, ...prev.slice(0, 5)]);
                    }
                } catch (e) {
                    console.error("Auto-Trade Failed", e);
                }
            };

            runAutoCycle();
            autoInterval = workerSetInterval(runAutoCycle, 15000);
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

    return (
        <div className="space-y-6">
            {toast && (
                <div className={`fixed top-4 right-4 px-4 py-2 rounded-lg text-white shadow-lg z-50 ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'}`}>
                    {toast.msg}
                </div>
            )}

            {/* Market-Hours Simulation Summary Bar */}
            <div className="bg-slate-900/60 backdrop-blur-sm p-4 rounded-2xl border border-indigo-500/20 shadow-xl flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-6">
                    <div>
                        <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest">Session Date</p>
                        <p className="text-sm font-mono font-bold text-white">{summary.date || 'Latest'}</p>
                    </div>
                    <div>
                        <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest">Closed Trades</p>
                        <p className="text-sm font-mono font-bold text-indigo-400">
                            {summary.closed_today_count} <span className="text-[10px] text-slate-500">({summary.wins}W / {summary.losses}L)</span>
                        </p>
                    </div>
                    <div>
                        <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest">Win Rate</p>
                        <p className="text-sm font-mono font-bold text-emerald-400">{Number(summary.win_rate || 0).toFixed(1)}%</p>
                    </div>
                    <div>
                        <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest">Session P&L</p>
                        <p className={`text-sm font-mono font-bold ${Number(summary.total_pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {Number(summary.total_pnl || 0) >= 0 ? '+' : ''}₹{Number(summary.total_pnl || 0).toLocaleString('en-IN')}
                        </p>
                    </div>
                    <div>
                        <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest">All-Time P&L ({summary.all_time_closed || 0})</p>
                        <p className={`text-sm font-mono font-bold ${Number(summary.all_time_pnl || 0) >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                            {Number(summary.all_time_pnl || 0) >= 0 ? '+' : ''}₹{Number(summary.all_time_pnl || 0).toLocaleString('en-IN')}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-[10px] font-black uppercase tracking-wider text-emerald-400">
                            {githubStatus.source} ({githubStatus.repo} #{githubStatus.latest_commit})
                        </span>
                    </div>
                    <button
                        onClick={handleSyncMarketHours}
                        disabled={syncing}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 text-xs font-bold transition-all"
                        title="Replay missed market hours and sync all backup data with GitHub"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                        <span>{syncing ? 'Syncing GitHub...' : 'Sync & Backup to GitHub'}</span>
                    </button>
                </div>
            </div>

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

            {/* Completed Market-Hours Simulation Trades */}
            <div className="bg-slate-900/50 backdrop-blur-sm p-6 rounded-2xl border border-indigo-500/20 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                            <CheckCircle className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white">Completed Market-Hours Simulation Trades</h3>
                            <p className="text-xs text-slate-400">
                                Automatically executed & settled during market hours (09:15–15:30 IST), including offline system replay
                            </p>
                        </div>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                        Showing latest {summary.recent_closed?.length || 0} of {summary.closed_today_count || 0} session trades
                    </span>
                </div>

                <div className="max-h-[360px] overflow-y-auto space-y-2 pr-1">
                    {(!summary.recent_closed || summary.recent_closed.length === 0) ? (
                        <div className="text-center py-8 text-slate-500 text-sm">
                            No completed simulation trades yet. Click "Sync Market Hours" to replay missed sessions.
                        </div>
                    ) : (
                        summary.recent_closed.map((trade, idx) => {
                            const isProfit = Number(trade.pnl || 0) >= 0;
                            const timeLabel = (trade.timestamp || '').replace('T', ' ').slice(0, 19);
                            return (
                                <div
                                    key={`${trade.trade_id || idx}-${idx}`}
                                    className="bg-slate-800/40 hover:bg-slate-800/70 transition-colors rounded-xl p-3 border border-slate-700/50 grid grid-cols-1 md:grid-cols-5 gap-2 items-center"
                                >
                                    <div className="text-xs font-mono text-slate-400">
                                        {timeLabel}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-400">
                                            {trade.side || 'BUY'}
                                        </span>
                                        <span className="font-bold text-sm text-white font-mono">{trade.symbol}</span>
                                    </div>
                                    <div className="text-xs font-mono text-slate-300">
                                        Qty {trade.quantity} • ₹{Number(trade.entry_price || 0).toFixed(2)} → ₹{Number(trade.exit_price || 0).toFixed(2)}
                                    </div>
                                    <div className="text-[11px] text-slate-400 truncate" title={trade.reasoning}>
                                        {trade.reasoning}
                                    </div>
                                    <div className={`text-right font-mono font-bold text-sm ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {isProfit ? '+' : ''}₹{Number(trade.pnl || 0).toFixed(2)}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};

export default PaperTrade;
