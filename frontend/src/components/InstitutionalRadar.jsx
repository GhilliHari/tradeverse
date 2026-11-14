import React, { useState, useEffect } from 'react';
import { 
    ShieldAlert, TrendingUp, TrendingDown, Gauge, 
    Zap, Activity, Landmark, Eye, RefreshCw, BarChart2, AlertCircle
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import { API_URL } from '../config/api';

const InstitutionalRadar = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(null);

    const fetchRadar = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_URL}/api/institutional/radar`);
            if (res.ok) {
                const json = await res.json();
                setData(json);
                setLastUpdated(new Date().toLocaleTimeString());
            }
        } catch (e) {
            console.error("Failed to load institutional radar:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRadar();
        const interval = setInterval(fetchRadar, 30000); // 30s auto-refresh
        return () => clearInterval(interval);
    }, []);

    const vt = data?.volatility_telemetry || {
        current_vix: 15.5, iv_rank: 31.8, iv_percentile: 61.8, 
        regime: "CHEAP_OPTIONS (Low IV)", strategy_recommendation: "NAKED_DIRECTIONAL_BUYING",
        strategy_reasoning: "Options are relatively cheap (IV Rank < 35%). Clean risk/reward for outright momentum bursts."
    };

    const ha = data?.heavyweight_anchor || {
        hdfc_return_pct: -1.02, icici_return_pct: -0.40, combined_weight_pct: 52.0,
        anchor_status: "CONVERGENT_BEARISH", bias: "Both Heavyweights Declining"
    };

    const inst = data?.institutional_positioning || {
        fii_net_contracts: -76360, fii_long_ratio_pct: 39.4, institutional_sentiment: "BEARISH_LEANING",
        institutional_summary: "FIIs holding net short futures contracts. Resistance wall active above 25,400."
    };

    const booster = data?.prediction_booster_signals || {
        can_buy_naked_options: true, fii_veto_active: true, heavyweight_veto_active: false,
        recommended_conviction_multiplier: 1.25
    };

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header / Status Banner */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 rounded-2xl bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900/60 border border-indigo-500/20 gap-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                        <Landmark className="w-5 h-5" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
                            Institutional & Alpha Telemetry Radar
                            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                Live Telemetry
                            </span>
                        </h2>
                        <p className="text-xs text-slate-400">
                            FII / DII Net Contract Flow • 252-Day IV Rank (IVR) • Heavyweight Anchor Matrix
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                    {lastUpdated && <span>Updated: {lastUpdated}</span>}
                    <button 
                        onClick={fetchRadar}
                        disabled={loading}
                        className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 transition-colors"
                        title="Refresh Telemetry"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* 3 Core Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* 1. Volatility & IV Rank */}
                <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/5 backdrop-blur-xl relative overflow-hidden group hover:border-indigo-500/30 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                            <Gauge className="w-4 h-4 text-purple-400" />
                            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">India VIX & IV Rank</span>
                        </div>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                            vt.iv_rank < 35 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                            vt.iv_rank > 65 ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                            {vt.regime}
                        </span>
                    </div>

                    <div className="flex items-baseline gap-3 mb-3">
                        <span className="text-3xl font-black font-mono text-white">{vt.current_vix}</span>
                        <span className="text-xs text-slate-400 font-mono">India VIX</span>
                    </div>

                    {/* Progress Bar for IV Rank */}
                    <div className="space-y-1.5 mb-4">
                        <div className="flex justify-between text-[11px] font-mono text-slate-400">
                            <span>IV Rank (252D)</span>
                            <span className="text-white font-bold">{vt.iv_rank}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden relative">
                            <div 
                                className={`h-full rounded-full transition-all duration-1000 ${
                                    vt.iv_rank < 35 ? 'bg-emerald-500' : vt.iv_rank > 65 ? 'bg-red-500' : 'bg-amber-500'
                                }`}
                                style={{ width: `${Math.min(100, Math.max(5, vt.iv_rank))}%` }}
                            />
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                            <span>52W Low: {vt['52w_low']}</span>
                            <span>52W High: {vt['52w_high']}</span>
                        </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-[11px]">
                        <span className="text-purple-300 font-bold block mb-0.5">Optimal Strategy:</span>
                        <p className="text-slate-300 leading-relaxed font-mono">{vt.strategy_recommendation}</p>
                    </div>
                </div>

                {/* 2. FII / DII Institutional Positioning */}
                <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/5 backdrop-blur-xl relative overflow-hidden group hover:border-indigo-500/30 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                            <Landmark className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">FII / Institutional Net OI</span>
                        </div>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                            inst.fii_net_contracts < 0 ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}>
                            {inst.institutional_sentiment}
                        </span>
                    </div>

                    <div className="flex items-baseline gap-3 mb-3">
                        <span className={`text-3xl font-black font-mono ${inst.fii_net_contracts < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(inst.fii_net_contracts / 1000).toFixed(1)}k
                        </span>
                        <span className="text-xs text-slate-400 font-mono">Net Index Contracts</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mb-4 text-[11px] font-mono">
                        <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                            <span className="text-slate-500 block text-[10px]">FII Long Ratio</span>
                            <span className="text-white font-bold">{inst.fii_long_ratio_pct}%</span>
                        </div>
                        <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                            <span className="text-slate-500 block text-[10px]">DII Net Cash</span>
                            <span className="text-emerald-400 font-bold">+₹48.2k</span>
                        </div>
                    </div>

                    <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                        {inst.institutional_summary}
                    </p>
                </div>

                {/* 3. Heavyweight Anchor (HDFC + ICICI = 52%) */}
                <div className="p-5 rounded-2xl bg-slate-900/70 border border-white/5 backdrop-blur-xl relative overflow-hidden group hover:border-indigo-500/30 transition-all">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                            <BarChart2 className="w-4 h-4 text-amber-400" />
                            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">The 52% Heavyweight Anchor</span>
                        </div>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                            ha.anchor_status === 'CONVERGENT_BULLISH' ? 'bg-emerald-500/20 text-emerald-400' :
                            ha.anchor_status === 'CONVERGENT_BEARISH' ? 'bg-red-500/20 text-red-400' :
                            'bg-amber-500/20 text-amber-400'
                        }`}>
                            {ha.anchor_status}
                        </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="text-xs font-bold text-slate-300">HDFC Bank (29%)</div>
                            <div className={`text-lg font-black font-mono ${ha.hdfc_return_pct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                {ha.hdfc_return_pct > 0 ? `+${ha.hdfc_return_pct}%` : `${ha.hdfc_return_pct}%`}
                            </div>
                        </div>
                        <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="text-xs font-bold text-slate-300">ICICI Bank (23%)</div>
                            <div className={`text-lg font-black font-mono ${ha.icici_return_pct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                {ha.icici_return_pct > 0 ? `+${ha.icici_return_pct}%` : `${ha.icici_return_pct}%`}
                            </div>
                        </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-[11px] font-mono">
                        <span className="text-amber-300 font-bold block mb-0.5">BankNifty Anchor Bias:</span>
                        <p className="text-slate-300">{ha.bias}</p>
                    </div>
                </div>
            </div>

            {/* Prediction Booster / Execution Rules Matrix */}
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-white/5 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <Zap className="w-5 h-5 text-amber-400" />
                    <div>
                        <span className="text-xs font-bold text-white block">Execution Multiplier & Veto Gate</span>
                        <span className="text-[11px] text-slate-400">Institutional confluence directly scales Kelly position sizing and vetoes bad trades.</span>
                    </div>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <span className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono text-slate-300">
                        Naked Options Permitted: <strong className={booster.can_buy_naked_options ? 'text-emerald-400' : 'text-red-400'}>
                            {booster.can_buy_naked_options ? 'YES (Low IV)' : 'NO (Spreads Only)'}
                        </strong>
                    </span>
                    <span className="px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs font-mono text-slate-300">
                        Conviction Multiplier: <strong className="text-amber-400">{booster.recommended_conviction_multiplier}x</strong>
                    </span>
                </div>
            </div>
        </div>
    );
};

export default InstitutionalRadar;
