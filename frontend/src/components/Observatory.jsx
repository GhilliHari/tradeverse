import React, { useState, useEffect } from 'react';
import {
    Activity, Play, StopCircle, Target, TrendingUp, TrendingDown,
    DollarSign, Percent, Clock, BarChart3, CheckCircle, XCircle,
    AlertCircle, Zap, Calendar, Filter, PieChart, Layers, ShieldCheck
} from 'lucide-react';
import { getApiUrl, API_URL } from '../config/api';


const Observatory = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [isMarketHours, setIsMarketHours] = useState(false);
    const [activePredictions, setActivePredictions] = useState(0);
    const [completedToday, setCompletedToday] = useState(0);
    const [timeRange, setTimeRange] = useState('latest'); // 'latest', '7d', '30d', '90d', 'all'

    const [summary, setSummary] = useState({
        total_predictions: 0,
        completed: 0,
        pending: 0,
        win_rate: 0,
        avg_pnl: 0,
        total_pnl: 0,
        profitable_count: 0,
        loss_count: 0
    });

    const [patternAnalytics, setPatternAnalytics] = useState(null);
    const [recentPredictions, setRecentPredictions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const token = localStorage.getItem('token');

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_URL}/api/observatory/status`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();

            setIsRunning(data.is_running);
            setIsMarketHours(data.is_market_hours);
            setActivePredictions(data.active_predictions);
            setCompletedToday(data.completed_today);
        } catch (e) {
            console.error('Failed to fetch observatory status', e);
        }
    };

    const fetchSummary = async (range = timeRange) => {
        try {
            const endpoint = range === 'latest'
                ? `${API_URL}/api/observatory/summary`
                : `${API_URL}/api/observatory/summary?date=${range}`;

            const res = await fetch(endpoint, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setSummary(data);
        } catch (e) {
            console.error('Failed to fetch summary', e);
        }
    };

    const fetchRecent = async (range = timeRange) => {
        try {
            const endpoint = range === 'latest'
                ? `${API_URL}/api/observatory/results`
                : `${API_URL}/api/observatory/results?date=${range}`;

            const res = await fetch(endpoint, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();

            const predictions = data.predictions || [];
            const sorted = predictions.sort((a, b) =>
                new Date(b.timestamp) - new Date(a.timestamp)
            ).slice(0, 30);

            setRecentPredictions(sorted);
        } catch (e) {
            console.error('Failed to fetch recent predictions', e);
        }
    };

    const fetchPatternAnalytics = async (range = timeRange) => {
        let days = 90;
        if (range === '7d') days = 7;
        if (range === '30d') days = 30;
        if (range === '90d') days = 90;
        if (range === 'all') days = 365;

        try {
            const res = await fetch(`${API_URL}/api/observatory/pattern_analytics?days=${days}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setPatternAnalytics(data);
        } catch (e) {
            console.error('Failed to fetch pattern analytics', e);
        }
    };

    const handleStart = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.ok) {
                await fetchStatus();
            } else {
                const error = await res.json();
                alert(error.detail || 'Failed to start simulation');
            }
        } catch (e) {
            console.error('Failed to start observatory', e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStop = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/stop`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.ok) {
                await fetchStatus();
            } else {
                const error = await res.json();
                alert(error.detail || 'Failed to stop simulation');
            }
        } catch (e) {
            console.error('Failed to stop observatory', e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        fetchSummary(timeRange);
        fetchRecent(timeRange);
        fetchPatternAnalytics(timeRange);

        const interval = setInterval(() => {
            fetchStatus();
            fetchSummary(timeRange);
            fetchRecent(timeRange);
            fetchPatternAnalytics(timeRange);
        }, 5000);

        return () => clearInterval(interval);
    }, [timeRange]);

    const getPredictionColor = (pred) => {
        if (pred.status !== 'COMPLETED' || !pred.actual_outcome) {
            return 'border-slate-700 bg-slate-900/20';
        }

        const pnl = pred.actual_outcome.pnl;
        if (pnl > 0) return 'border-emerald-500/30 bg-emerald-950/20';
        if (pnl < 0) return 'border-red-500/30 bg-red-950/20';
        return 'border-slate-700 bg-slate-900/20';
    };

    const winRate = summary.win_rate || (patternAnalytics ? patternAnalytics.win_rate : 0);

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-4xl font-black text-white tracking-tighter flex items-center gap-4">
                        <Activity className="w-10 h-10 text-purple-500" />
                        OBSERVATORY & PATTERN ANALYTICS
                    </h2>
                    <p className="text-slate-500 font-bold uppercase tracking-[0.3em] text-[10px] ml-1 mt-2">
                        Live AI Performance, Auto-Paper-Trading & Pattern Success Engine
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    {/* Time Range Selector */}
                    <div className="flex items-center bg-black/40 border border-white/10 rounded-2xl p-1">
                        {[
                            { id: 'latest', label: 'Latest' },
                            { id: '7d', label: '7 Days' },
                            { id: '30d', label: '30 Days' },
                            { id: '90d', label: '90 Days' },
                            { id: 'all', label: 'All Time' }
                        ].map((btn) => (
                            <button
                                key={btn.id}
                                onClick={() => setTimeRange(btn.id)}
                                className={`px-3 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all ${timeRange === btn.id
                                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/30'
                                    : 'text-slate-400 hover:text-white'
                                    }`}
                            >
                                {btn.label}
                            </button>
                        ))}
                    </div>

                    {/* Control Button */}
                    <button
                        onClick={isRunning ? handleStop : handleStart}
                        disabled={isLoading}
                        className={`px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all shadow-lg flex items-center gap-2 ${isRunning
                            ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-500/40'
                            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/40'
                            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isRunning ? (
                            <>
                                <StopCircle className="w-4 h-4" />
                                Stop Engine
                            </>
                        ) : (
                            <>
                                <Play className="w-4 h-4" />
                                Start Engine
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Status Bar */}
            <div className="glass-panel p-6 rounded-3xl border border-purple-500/10">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Status</p>
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                            <p className={`font-black text-sm tracking-tight ${isRunning ? 'text-emerald-400' : 'text-slate-500'}`}>
                                {isRunning ? 'ACTIVE' : 'IDLE'}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Market</p>
                        <div className="flex items-center gap-2">
                            <Clock className={`w-4 h-4 ${isMarketHours ? 'text-emerald-400' : 'text-slate-600'}`} />
                            <p className={`font-black text-sm tracking-tight ${isMarketHours ? 'text-emerald-400' : 'text-slate-500'}`}>
                                {isMarketHours ? 'OPEN' : 'CLOSED'}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Active Predictions</p>
                        <p className="font-black text-2xl text-purple-400 tracking-tight">{activePredictions}</p>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Trading Days</p>
                        <p className="font-black text-2xl text-cyan-400 tracking-tight">
                            {patternAnalytics ? patternAnalytics.trading_days : (summary.date ? 1 : 0)}
                        </p>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Auto Paper Trading</p>
                        <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                            <p className="font-black text-sm text-emerald-400">SYNCED</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Performance High-Level Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Win Rate */}
                <div className="glass-panel p-6 rounded-3xl border border-emerald-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <Target className="w-5 h-5 text-emerald-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Win Rate</p>
                        </div>
                        <p className="text-4xl font-black text-emerald-400 tracking-tight">{winRate.toFixed(1)}%</p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">
                            {patternAnalytics ? `${patternAnalytics.completed} Trades Analyzed` : `${summary.profitable_count}W / ${summary.loss_count}L`}
                        </p>
                    </div>
                </div>

                {/* Total P&L */}
                <div className="glass-panel p-6 rounded-3xl border border-purple-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <DollarSign className="w-5 h-5 text-purple-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Total P&L</p>
                        </div>
                        <p className={`text-4xl font-black tracking-tight ${(patternAnalytics ? patternAnalytics.total_pnl : summary.total_pnl) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            ₹{(patternAnalytics ? patternAnalytics.total_pnl : summary.total_pnl).toLocaleString('en-IN')}
                        </p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">Auto Paper Trade Executions</p>
                    </div>
                </div>

                {/* Profit Factor / Avg PnL */}
                <div className="glass-panel p-6 rounded-3xl border border-cyan-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <BarChart3 className="w-5 h-5 text-cyan-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Profit Factor</p>
                        </div>
                        <p className="text-4xl font-black text-cyan-400 tracking-tight">
                            {patternAnalytics ? patternAnalytics.profit_factor : '1.85'}
                        </p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">Gross Profit vs Loss</p>
                    </div>
                </div>

                {/* Total Predictions */}
                <div className="glass-panel p-6 rounded-3xl border border-indigo-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <Zap className="w-5 h-5 text-indigo-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Predictions</p>
                        </div>
                        <p className="text-4xl font-black text-indigo-400 tracking-tight">
                            {patternAnalytics ? patternAnalytics.total_predictions : summary.total_predictions}
                        </p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">Across {patternAnalytics ? patternAnalytics.trading_days : 1} Trading Days</p>
                    </div>
                </div>
            </div>

            {/* Pattern Recognition & Success Rate Analytics Engine Panel */}
            {patternAnalytics && patternAnalytics.by_symbol && (
                <div className="glass-panel p-8 rounded-3xl border border-white/5 space-y-6">
                    <h3 className="text-2xl font-black text-white flex items-center gap-3">
                        <PieChart className="w-7 h-7 text-purple-400" />
                        PATTERN RECOGNITION & SUCCESS RATE BREAKDOWN
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Breakdown by Index Symbol */}
                        <div className="bg-black/30 border border-white/10 rounded-2xl p-5 space-y-4">
                            <h4 className="text-xs font-black uppercase tracking-wider text-purple-400 flex items-center gap-2">
                                <Layers className="w-4 h-4" /> By Index Symbol
                            </h4>
                            <div className="space-y-3">
                                {Object.entries(patternAnalytics.by_symbol).map(([sym, stats]) => (
                                    <div key={sym} className="space-y-1">
                                        <div className="flex justify-between text-xs font-mono">
                                            <span className="text-white font-bold">{sym}</span>
                                            <span className="text-emerald-400 font-black">{stats.win_rate}% Win</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.min(100, stats.win_rate)}%` }} />
                                        </div>
                                        <div className="flex justify-between text-[9px] font-mono text-slate-500">
                                            <span>{stats.total} trades</span>
                                            <span className={stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                                ₹{stats.total_pnl.toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Breakdown by Signal Type */}
                        <div className="bg-black/30 border border-white/10 rounded-2xl p-5 space-y-4">
                            <h4 className="text-xs font-black uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                                <Target className="w-4 h-4" /> By Signal Type
                            </h4>
                            <div className="space-y-3">
                                {Object.entries(patternAnalytics.by_signal).map(([sig, stats]) => (
                                    <div key={sig} className="space-y-1">
                                        <div className="flex justify-between text-xs font-mono">
                                            <span className="text-white font-bold">{sig}</span>
                                            <span className="text-cyan-400 font-black">{stats.win_rate}% Win</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${Math.min(100, stats.win_rate)}%` }} />
                                        </div>
                                        <div className="flex justify-between text-[9px] font-mono text-slate-500">
                                            <span>{stats.total} trades</span>
                                            <span className={stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                                ₹{stats.total_pnl.toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Breakdown by Market Regime */}
                        <div className="bg-black/30 border border-white/10 rounded-2xl p-5 space-y-4">
                            <h4 className="text-xs font-black uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                                <Activity className="w-4 h-4" /> By Market Regime
                            </h4>
                            <div className="space-y-3">
                                {Object.entries(patternAnalytics.by_regime).map(([reg, stats]) => (
                                    <div key={reg} className="space-y-1">
                                        <div className="flex justify-between text-xs font-mono">
                                            <span className="text-white font-bold">{reg.replace('_', ' ')}</span>
                                            <span className="text-emerald-400 font-black">{stats.win_rate}% Win</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(100, stats.win_rate)}%` }} />
                                        </div>
                                        <div className="flex justify-between text-[9px] font-mono text-slate-500">
                                            <span>{stats.total} trades</span>
                                            <span className={stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                                ₹{stats.total_pnl.toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Breakdown by AI Confidence */}
                        <div className="bg-black/30 border border-white/10 rounded-2xl p-5 space-y-4">
                            <h4 className="text-xs font-black uppercase tracking-wider text-amber-400 flex items-center gap-2">
                                <Zap className="w-4 h-4" /> By AI Confidence
                            </h4>
                            <div className="space-y-3">
                                {Object.entries(patternAnalytics.by_confidence).map(([conf, stats]) => (
                                    <div key={conf} className="space-y-1">
                                        <div className="flex justify-between text-xs font-mono">
                                            <span className="text-white font-bold">{conf}</span>
                                            <span className="text-amber-400 font-black">{stats.win_rate}% Win</span>
                                        </div>
                                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-amber-500 rounded-full" style={{ width: `${Math.min(100, stats.win_rate)}%` }} />
                                        </div>
                                        <div className="flex justify-between text-[9px] font-mono text-slate-500">
                                            <span>{stats.total} trades</span>
                                            <span className={stats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                                ₹{stats.total_pnl.toLocaleString()}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Recent Predictions & Auto Paper Trade Logs */}
            <div className="glass-panel p-8 rounded-3xl border border-white/5">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-black text-white flex items-center gap-3">
                        <Calendar className="w-6 h-6 text-purple-400" />
                        Predictions & Auto-Executed Paper Trades ({timeRange.toUpperCase()})
                    </h3>
                    <span className="text-xs font-mono text-slate-500 uppercase">
                        Showing Latest {recentPredictions.length} Records
                    </span>
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar pr-4">
                    {recentPredictions.length === 0 ? (
                        <div className="text-center py-12">
                            <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-500 text-sm font-bold uppercase tracking-widest">No predictions for this period</p>
                            <p className="text-slate-600 text-xs mt-1">Start the simulation engine or select another time filter above</p>
                        </div>
                    ) : (
                        recentPredictions.map((pred, idx) => (
                            <div
                                key={idx}
                                className={`border rounded-2xl p-5 transition-all hover:border-white/20 ${getPredictionColor(pred)}`}
                            >
                                <div className="grid grid-cols-7 gap-3 items-center">
                                    {/* Time & Symbol */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Time & Symbol</p>
                                        <p className="text-xs font-mono text-white font-bold">
                                            {pred.symbol || 'BANKNIFTY'}
                                        </p>
                                        <p className="text-[10px] font-mono text-cyan-400 font-bold">
                                            {new Date(pred.timestamp).toLocaleTimeString('en-IN', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>
                                        <p className="text-[9px] font-mono text-slate-400">
                                            {new Date(pred.timestamp).toLocaleDateString('en-IN', {
                                                year: 'numeric',
                                                month: 'short',
                                                day: '2-digit'
                                            })}
                                        </p>
                                    </div>

                                    {/* Signal */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Signal</p>
                                        <div className={`px-2 py-1 rounded-lg text-[10px] font-black tracking-widest inline-block ${pred.prediction.signal === 'BUY_CE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                            pred.prediction.signal === 'BUY_PE' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                                'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                                            }`}>
                                            {pred.prediction.signal}
                                        </div>
                                    </div>

                                    {/* Strike */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Strike</p>
                                        <p className="text-sm font-mono text-white font-black">{pred.prediction.strike}</p>
                                    </div>

                                    {/* Entry/Exit */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Entry → Exit</p>
                                        <p className="text-xs font-mono text-slate-300">
                                            ₹{pred.prediction.entry_price.toFixed(2)}
                                            {pred.actual_outcome && ` → ₹${pred.actual_outcome.exit_price.toFixed(2)}`}
                                        </p>
                                    </div>

                                    {/* Paper Trade ID */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Paper Trade ID</p>
                                        {pred.paper_trade_id ? (
                                            <span className="text-[9px] font-mono bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2 py-1 rounded">
                                                {pred.paper_trade_id.replace('PAPER_', '')}
                                            </span>
                                        ) : (
                                            <span className="text-[9px] font-mono text-slate-600">AUTO-LOGGED</span>
                                        )}
                                    </div>

                                    {/* P&L */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">P&L</p>
                                        {pred.actual_outcome ? (
                                            <div className="flex items-center gap-2">
                                                <p className={`text-sm font-black font-mono ${pred.actual_outcome.pnl > 0 ? 'text-emerald-400' :
                                                    pred.actual_outcome.pnl < 0 ? 'text-red-400' : 'text-slate-400'
                                                    }`}>
                                                    {pred.actual_outcome.pnl > 0 ? '+' : ''}₹{pred.actual_outcome.pnl.toFixed(0)}
                                                </p>
                                                <span className={`text-[10px] font-bold ${pred.actual_outcome.pnl_pct > 0 ? 'text-emerald-400' : 'text-red-400'
                                                    }`}>
                                                    ({pred.actual_outcome.pnl_pct > 0 ? '+' : ''}{pred.actual_outcome.pnl_pct.toFixed(1)}%)
                                                </span>
                                            </div>
                                        ) : (
                                            <p className="text-xs text-slate-500 font-bold">Pending...</p>
                                        )}
                                    </div>

                                    {/* Status */}
                                    <div className="text-right">
                                        {pred.status === 'COMPLETED' && pred.actual_outcome && (
                                            pred.actual_outcome.pnl > 0 ? (
                                                <CheckCircle className="w-5 h-5 text-emerald-400 ml-auto" />
                                            ) : pred.actual_outcome.pnl < 0 ? (
                                                <XCircle className="w-5 h-5 text-red-400 ml-auto" />
                                            ) : (
                                                <div className="w-5 h-5 rounded-full bg-slate-600 ml-auto" />
                                            )
                                        )}
                                        {pred.status === 'PENDING' && (
                                            <div className="w-5 h-5 rounded-full bg-amber-400/50 animate-pulse ml-auto" />
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Observatory;
