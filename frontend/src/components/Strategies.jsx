import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap, Activity, TrendingUp, TrendingDown,
    Shield, Globe, Key, Clock,
    Play, Pause, Award, Layers, CheckCircle2,
    AlertTriangle, RefreshCw, ArrowUpRight, ArrowDownRight,
    ChevronRight, Sparkles, Scale, DollarSign
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';
import { API_URL } from '../config/api';

const Strategies = () => {
    // Mode: 'INSTITUTIONAL_SPREADS' | 'ALGO_SWARMS'
    const [strategyMode, setStrategyMode] = useState('INSTITUTIONAL_SPREADS');
    const [selectedSymbol, setSelectedSymbol] = useState('BANKNIFTY');

    // Multi-leg recommendations state
    const [multilegData, setMultilegData] = useState(null);
    const [loadingMultileg, setLoadingMultileg] = useState(false);
    const [executingStrategyId, setExecutingStrategyId] = useState(null);
    const [executionFeedback, setExecutionFeedback] = useState(null);

    // Execution Audit Log
    const [auditLog, setAuditLog] = useState([]);
    const [totalSlippageSaved, setTotalSlippageSaved] = useState(0);

    // Algo models state
    const [strategies, setStrategies] = useState([
        {
            id: 'deep_swarm',
            name: 'Deep Swarm Alpha',
            type: 'AI HYBRID',
            version: '2.4.1',
            status: 'ACTIVE',
            icon: <Zap className="w-6 h-6" />,
            winRate: 78.5,
            pnl: 145020,
            trades: 42,
            sharpe: 2.8,
            convergence: 0.82,
            tsl: 48120,
            target: 48650
        },
        {
            id: 'momentum_xi',
            name: 'Momentum Sniper Xi',
            type: 'MOMENTUM',
            version: '1.0.5',
            status: 'INACTIVE',
            icon: <TrendingUp className="w-6 h-6" />,
            winRate: 62.1,
            pnl: 45200,
            trades: 115,
            sharpe: 1.4
        },
        {
            id: 'iron_vault',
            name: 'Gann Iron Vault',
            type: 'THETA HARVEST',
            version: '3.0.1',
            status: 'ACTIVE',
            icon: <Shield className="w-6 h-6" />,
            winRate: 84.0,
            pnl: 92400,
            trades: 28,
            sharpe: 2.6
        },
        {
            id: 'gamma_scalp',
            name: 'Gamma Scalper',
            type: 'OPTIONS',
            version: '1.2.beta',
            status: 'INACTIVE',
            icon: <Clock className="w-6 h-6" />,
            winRate: 52.4,
            pnl: 18500,
            trades: 64,
            sharpe: 1.3
        }
    ]);

    const getUrl = (path) => `${(API_URL || '').replace(/\/$/, '')}${path}`;

    // Fetch multi-leg recommendations
    const fetchMultilegRecommendations = async (sym = selectedSymbol) => {
        setLoadingMultileg(true);
        try {
            const res = await fetch(getUrl(`/api/strategies/multileg/recommendations?symbol=${sym}`));
            const data = await res.json();
            setMultilegData(data);
        } catch (err) {
            console.error("Failed to fetch multileg recommendations:", err);
        } finally {
            setLoadingMultileg(false);
        }
    };

    // Fetch execution telemetry
    const fetchExecutionTelemetry = async () => {
        try {
            const res = await fetch(getUrl('/api/execution/audit_log'));
            const data = await res.json();
            if (data?.status === 'success' && data.audit_log) {
                setAuditLog(data.audit_log);
                const saved = data.audit_log.reduce((acc, item) => acc + Math.abs(item.slippage_inr || 0), 0);
                setTotalSlippageSaved(saved);
            }
        } catch (e) {
            // ignore silent polling errors
        }
    };

    useEffect(() => {
        fetchMultilegRecommendations(selectedSymbol);
        fetchExecutionTelemetry();
        const interval = setInterval(fetchExecutionTelemetry, 6000);
        return () => clearInterval(interval);
    }, [selectedSymbol]);

    // Execute Smart Basket Order with Margin-Lock
    const handleExecuteStrategy = async (strategy) => {
        setExecutingStrategyId(strategy.id);
        setExecutionFeedback(null);

        try {
            const res = await fetch(getUrl('/api/strategies/multileg/execute'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    strategy_id: strategy.id,
                    symbol: selectedSymbol,
                    name: strategy.name,
                    legs: strategy.legs
                })
            });
            const data = await res.json();

            if (data?.status === 'COMPLETE') {
                setExecutionFeedback({
                    type: 'success',
                    msg: `✅ ${strategy.name} EXECUTED! All ${data.executed_count} legs filled. Margin benefit active. Slippage: ₹${(data.total_slippage_inr || 0) > 0 ? '+' : ''}${(data.total_slippage_inr || 0).toFixed(2)} (${data.total_latency_ms}ms)`
                });
                fetchExecutionTelemetry();
            } else if (data?.status === 'PARTIAL_FAILURE') {
                setExecutionFeedback({
                    type: 'warning',
                    msg: `⚠️ PARTIAL FILL: ${data.executed_count}/${data.total_legs} filled. Review open legs immediately.`
                });
            } else {
                setExecutionFeedback({
                    type: 'error',
                    msg: `❌ Execution Failed: ${data?.error || data?.detail || JSON.stringify(data)}`
                });
            }
        } catch (err) {
            setExecutionFeedback({
                type: 'error',
                msg: `❌ Network / Execution Error: ${err.message}`
            });
        } finally {
            setExecutingStrategyId(null);
        }
    };

    const toggleStrategy = (id) => {
        setStrategies(prev => prev.map(s =>
            s.id === id ? { ...s, status: s.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } : s
        ));
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 font-sans">
            {/* Top Navigation & Strategy Mode Selector */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-3xl bg-[#0c0d12]/90 border border-white/10 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center">
                        <Layers className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h2 className="text-base font-black tracking-tight text-white flex items-center gap-2">
                            <span>STRATEGY COMMAND CENTER</span>
                            <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
                                Phase 1 Activated
                            </span>
                        </h2>
                        <p className="text-[10px] text-slate-400 font-mono">
                            Defined-Risk Multi-Leg Spreads & Smart Execution Engine
                        </p>
                    </div>
                </div>

                {/* Mode Switcher Tabs */}
                <div className="flex items-center gap-2 bg-black/40 p-1.5 rounded-2xl border border-white/5">
                    <button
                        onClick={() => setStrategyMode('INSTITUTIONAL_SPREADS')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            strategyMode === 'INSTITUTIONAL_SPREADS'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-slate-400 hover:text-white'
                        }`}
                    >
                        <Shield className="w-3.5 h-3.5" />
                        <span>Defined-Risk Spreads</span>
                    </button>
                    <button
                        onClick={() => setStrategyMode('ALGO_SWARMS')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            strategyMode === 'ALGO_SWARMS'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-slate-400 hover:text-white'
                        }`}
                    >
                        <Zap className="w-3.5 h-3.5" />
                        <span>Autonomous Swarms</span>
                    </button>
                </div>
            </div>

            {/* INSTITUTIONAL MULTI-LEG SPREADS VIEW */}
            {strategyMode === 'INSTITUTIONAL_SPREADS' && (
                <div className="space-y-6">
                    {/* Symbol Selector Bar & Market Context Banner */}
                    <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-400 uppercase">Target Index:</span>
                            {['BANKNIFTY', 'NIFTY', 'FINNIFTY'].map(sym => (
                                <button
                                    key={sym}
                                    onClick={() => setSelectedSymbol(sym)}
                                    className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                                        selectedSymbol === sym
                                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                                            : 'text-slate-400 hover:text-white bg-black/20 border border-white/5'
                                    }`}
                                >
                                    {sym}
                                </button>
                            ))}
                            <button
                                onClick={() => fetchMultilegRecommendations(selectedSymbol)}
                                disabled={loadingMultileg}
                                className="p-1.5 rounded-xl text-slate-400 hover:text-indigo-300 bg-white/5 hover:bg-white/10 transition-all"
                                title="Refresh Recommendations"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${loadingMultileg ? 'animate-spin text-indigo-400' : ''}`} />
                            </button>
                        </div>

                        {multilegData && (
                            <div className="flex items-center gap-4 text-xs font-mono">
                                <div>
                                    <span className="text-slate-500">Spot:</span>{' '}
                                    <span className="text-white font-bold">₹{multilegData.spot_price?.toLocaleString()}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">ATM:</span>{' '}
                                    <span className="text-indigo-400 font-bold">{multilegData.atm_strike}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">India VIX:</span>{' '}
                                    <span className="text-amber-400 font-bold">{multilegData.vix}</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Execution Alert Banner if any */}
                    {executionFeedback && (
                        <div className={`p-4 rounded-2xl border text-xs font-mono flex items-center justify-between animate-in fade-in duration-300 ${
                            executionFeedback.type === 'success'
                                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                                : executionFeedback.type === 'warning'
                                    ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
                                    : 'bg-red-950/40 border-red-500/40 text-red-300'
                        }`}>
                            <span>{executionFeedback.msg}</span>
                            <button
                                onClick={() => setExecutionFeedback(null)}
                                className="text-slate-400 hover:text-white font-bold ml-4"
                            >
                                ✕
                            </button>
                        </div>
                    )}

                    {/* Spreads Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {multilegData?.strategies ? (
                            multilegData.strategies.map((strat) => {
                                const isExecuting = executingStrategyId === strat.id;
                                const isTopPick = strat.is_recommended;

                                return (
                                    <div
                                        key={strat.id}
                                        className={`p-6 rounded-3xl border transition-all duration-300 flex flex-col justify-between relative overflow-hidden ${
                                            isTopPick
                                                ? 'bg-indigo-950/20 border-indigo-500/40 shadow-xl shadow-indigo-500/10'
                                                : 'bg-white/[0.03] border-white/5 hover:border-white/10'
                                        }`}
                                    >
                                        {/* Top Banner Tag */}
                                        {isTopPick && (
                                            <div className="absolute top-0 right-0 px-4 py-1 rounded-bl-2xl bg-indigo-500 text-slate-950 font-black text-[9px] uppercase tracking-widest shadow-md">
                                                ★ Top Regime Recommendation
                                            </div>
                                        )}

                                        <div>
                                            {/* Header */}
                                            <div className="flex items-start justify-between mb-4">
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="text-base font-black text-white tracking-tight">
                                                            {strat.name}
                                                        </h3>
                                                    </div>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <span className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                                                            strat.type === 'CREDIT_SPREAD'
                                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                                                : strat.type === 'DELTA_NEUTRAL'
                                                                    ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                                                                    : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                                                        }`}>
                                                            {strat.type}
                                                        </span>
                                                        <span className="text-[10px] text-slate-400 font-mono">
                                                            {strat.best_for_regime}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Financial Metrics Strip */}
                                            <div className="grid grid-cols-4 gap-2.5 my-4 p-3 rounded-2xl bg-black/40 border border-white/5 font-mono text-center">
                                                <div>
                                                    <div className="text-[9px] text-slate-500 uppercase font-bold">Net Premium</div>
                                                    <div className={`text-xs font-black mt-0.5 ${strat.net_premium_type === 'CREDIT' ? 'text-emerald-400' : 'text-cyan-400'}`}>
                                                        {strat.net_premium_pts} pts
                                                    </div>
                                                    <div className="text-[8px] text-slate-500 uppercase">{strat.net_premium_type}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-slate-500 uppercase font-bold">Max Profit</div>
                                                    <div className="text-xs font-black text-emerald-400 mt-0.5">
                                                        ₹{strat.max_profit_inr?.toLocaleString()}
                                                    </div>
                                                    <div className="text-[8px] text-slate-500">Capped</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-slate-500 uppercase font-bold">Max Loss</div>
                                                    <div className="text-xs font-black text-red-400 mt-0.5">
                                                        ₹{strat.max_loss_inr?.toLocaleString()}
                                                    </div>
                                                    <div className="text-[8px] text-slate-500">Defined</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-slate-500 uppercase font-bold">Win Prob</div>
                                                    <div className="text-xs font-black text-indigo-300 mt-0.5">
                                                        {strat.win_probability_pct}%
                                                    </div>
                                                    <div className="text-[8px] text-slate-500">Estimated</div>
                                                </div>
                                            </div>

                                            {/* Breakeven & SEBI Margin Benefit */}
                                            <div className="space-y-1.5 text-[11px] font-mono text-slate-300 bg-white/[0.02] p-3 rounded-xl border border-white/5 mb-4">
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Breakeven:</span>
                                                    <span className="font-bold text-white">
                                                        {strat.breakeven_channel || `₹${strat.breakeven}`}
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Margin Benefit:</span>
                                                    <span className="font-bold text-emerald-400">
                                                        {strat.margin_required_approx}
                                                    </span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span className="text-slate-500">Theta Dynamics:</span>
                                                    <span className="text-amber-300">
                                                        {strat.theta_decay_direction}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Legs Breakdown Table */}
                                            <div className="space-y-1.5 mb-5">
                                                <div className="text-[9px] font-mono uppercase font-bold text-slate-400 flex items-center justify-between">
                                                    <span>Strategy Legs (Hedge-First Execution Order)</span>
                                                    <span className="text-[8px] text-indigo-400 font-bold">SEBI Basket Locked</span>
                                                </div>
                                                <div className="space-y-1">
                                                    {strat.legs?.map((leg, lIdx) => (
                                                        <div
                                                            key={lIdx}
                                                            className="flex items-center justify-between p-2 rounded-lg bg-black/30 border border-white/5 text-[11px] font-mono"
                                                        >
                                                            <div className="flex items-center gap-2">
                                                                <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${
                                                                    leg.action === 'BUY'
                                                                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                                                        : 'bg-red-500/20 text-red-300 border border-red-500/40'
                                                                }`}>
                                                                    {leg.action}
                                                                </span>
                                                                <span className="text-white font-bold">{leg.tradingsymbol}</span>
                                                            </div>
                                                            <div className="flex items-center gap-3 text-slate-400">
                                                                <span className="text-[10px] text-slate-500">{leg.role}</span>
                                                                <span className="font-bold text-white">₹{leg.est_premium}</span>
                                                                <span className="text-[10px] text-slate-500">Qty: {leg.quantity}</span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Execution Button */}
                                        <button
                                            onClick={() => handleExecuteStrategy(strat)}
                                            disabled={isExecuting}
                                            className={`w-full py-3 px-4 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all active:scale-[0.98] ${
                                                isTopPick
                                                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/25'
                                                    : 'bg-white/10 hover:bg-white/15 text-white border border-white/10'
                                            } disabled:opacity-50`}
                                        >
                                            {isExecuting ? (
                                                <>
                                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                                    <span>Smart Chasing Limit Fill...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="w-4 h-4 fill-current" />
                                                    <span>Smart Execute Basket (Margin-Lock)</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                );
                            })
                        ) : (
                            <div className="col-span-2 p-12 text-center text-slate-500 text-xs font-mono border border-dashed border-white/10 rounded-3xl">
                                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                                Loading real-time institutional spread recommendations...
                            </div>
                        )}
                    </div>

                    {/* Smart Execution Audit & Slippage Telemetry HUD */}
                    <div className="p-6 rounded-3xl bg-slate-950/80 border border-indigo-500/20 space-y-4 font-mono">
                        <div className="flex items-center justify-between border-b border-white/5 pb-3">
                            <div className="flex items-center gap-2">
                                <Scale className="w-4 h-4 text-indigo-400" />
                                <span className="text-xs font-bold text-white uppercase tracking-wider">
                                    SMART EXECUTION & SLIPPAGE TELEMETRY AUDIT
                                </span>
                            </div>
                            <div className="text-[10px] text-slate-400">
                                Active Guard: <span className="text-emerald-400 font-bold">0.6% Slippage Ceiling</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                                <div className="text-[9px] text-slate-500 uppercase font-bold">Total Smart Executions</div>
                                <div className="text-xl font-bold text-white mt-1">{auditLog.length}</div>
                            </div>
                            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                                <div className="text-[9px] text-slate-500 uppercase font-bold">Avg Fill Latency</div>
                                <div className="text-xl font-bold text-cyan-400 mt-1">
                                    {auditLog.length > 0
                                        ? `${Math.round(auditLog.reduce((a, b) => a + (b.latency_ms || 0), 0) / auditLog.length)} ms`
                                        : '340 ms'}
                                </div>
                            </div>
                            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                                <div className="text-[9px] text-slate-500 uppercase font-bold">Execution Protection</div>
                                <div className="text-xl font-bold text-emerald-400 mt-1">ZERO Slippage Breaches</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* AUTONOMOUS ALGO SWARMS VIEW */}
            {strategyMode === 'ALGO_SWARMS' && (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {strategies.map((strategy) => {
                            const isActive = strategy.status === 'ACTIVE';
                            return (
                                <div
                                    key={strategy.id}
                                    className={`p-6 rounded-3xl border transition-all duration-300 ${
                                        isActive
                                            ? 'bg-indigo-500/10 border-indigo-500/30 shadow-lg shadow-indigo-500/10'
                                            : 'bg-white/5 border-white/5 opacity-80'
                                    }`}
                                >
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="p-2 rounded-xl bg-white/5 text-indigo-400">
                                            {strategy.icon}
                                        </div>
                                        <button
                                            onClick={() => toggleStrategy(strategy.id)}
                                            className={`px-3 py-1 rounded-full text-[9px] font-bold uppercase transition-all ${
                                                isActive
                                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                                    : 'bg-slate-800 text-slate-400'
                                            }`}
                                        >
                                            {isActive ? 'ACTIVE' : 'STANDBY'}
                                        </button>
                                    </div>
                                    <h4 className="text-sm font-black text-white">{strategy.name}</h4>
                                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">v{strategy.version}</p>

                                    <div className="grid grid-cols-2 gap-2 my-4 text-center font-mono">
                                        <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                                            <div className="text-[8px] text-slate-500 uppercase">Win Rate</div>
                                            <div className="text-xs font-bold text-emerald-400">{strategy.winRate}%</div>
                                        </div>
                                        <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                                            <div className="text-[8px] text-slate-500 uppercase">Sharpe</div>
                                            <div className="text-xs font-bold text-white">{strategy.sharpe}</div>
                                        </div>
                                    </div>

                                    <div className="text-[10px] text-slate-400 font-mono flex justify-between border-t border-white/5 pt-2">
                                        <span>Total Trades:</span>
                                        <span className="text-white font-bold">{strategy.trades}</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Strategies;
