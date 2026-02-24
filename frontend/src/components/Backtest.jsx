import React, { useState } from 'react';
import {
    Activity, Play, Server, Database, TrendingUp,
    Shield, CheckCircle, AlertTriangle, Cpu, Target
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// BASE API URL
const getApiUrl = () => {
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved) return saved.replace(/\/$/, '');
    } catch (e) { }
    return import.meta.env.VITE_API_URL || "";
};
const API_URL = getApiUrl();

const Backtest = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [result, setResult] = useState(null);
    const [modelType, setModelType] = useState('daily_12y');
    const [symbol, setSymbol] = useState('^NSEBANK');

    const runBacktest = async () => {
        setIsLoading(true);
        setResult(null);
        try {
            const res = await fetch(`${API_URL}/api/ai/backtest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol, model_type: modelType })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setResult(data.metrics);
            } else {
                alert("Backtest Failed: " + data.detail);
            }
        } catch (e) {
            alert("Network Error: " + e.message);
        }
        setIsLoading(false);
    };

    const refreshData = async () => {
        setIsRefreshing(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/api/data/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await res.json();
            if (data.status === 'started') {
                alert("Data Refresh Started: Check logs for progress.");
            } else {
                alert("Refresh Failed: " + data.message);
            }
        } catch (e) {
            alert("Network Error: " + e.message);
        }
        setIsRefreshing(false);
    };

    const getFreshnessColor = (hours) => {
        if (hours < 24) return "text-emerald-400";
        if (hours < 48) return "text-amber-400";
        return "text-red-400";
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* Control Panel */}
            <HUDCard title="NEURAL BACKTEST ENGINE v2.1" neonColor="amber">
                <div className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-6">
                        <div className="w-16 h-16 bg-amber-500/10 rounded-full flex items-center justify-center border border-amber-500/20 shadow-[0_0_20px_rgba(245,158,11,0.1)]">
                            <Cpu className={`w-8 h-8 text-amber-500 ${isLoading ? 'animate-spin' : ''}`} />
                        </div>
                        <div>
                            <div className="text-2xl font-black text-white font-mono tracking-tight">
                                HISTORICAL VALIDATION
                            </div>
                            <div className="text-[10px] font-bold uppercase text-slate-500 mt-1 flex items-center gap-2">
                                <Database className="w-3 h-3" />
                                {modelType.includes('daily') ? '12 YEARS DATA (10Y TRAIN / 2Y TEST)' :
                                    modelType.includes('1y') ? '1 YEAR DATA (SNP)' :
                                        modelType.includes('1m') ? '1 MONTH DATA (SNP)' : '7 DAYS DATA (SNP)'}
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <select
                            value={modelType}
                            onChange={(e) => setModelType(e.target.value)}
                            className="bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-widest text-slate-300 focus:outline-none focus:border-amber-500/50"
                        >
                            <option value="daily_12y">Daily Strategist (12 Years)</option>
                            <option value="intraday_7d">Intraday Sniper (7 Days)</option>
                            <option value="intraday_1m">1 Month Sniper (30 Days)</option>
                            <option value="intraday_1y">1 Year Sniper (365 Days)</option>
                        </select>

                        <button
                            onClick={refreshData}
                            disabled={isRefreshing}
                            className={`px-4 py-3 rounded-xl font-bold uppercase tracking-widest text-xs flex items-center gap-2 transition-all border border-white/10 hover:bg-white/5 ${isRefreshing ? 'opacity-50' : ''}`}
                            title="Refresh Data Source"
                        >
                            <Server className={`w-4 h-4 text-slate-400 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </button>

                        <button
                            onClick={runBacktest}
                            disabled={isLoading}
                            className={`px-6 py-3 rounded-xl font-black uppercase tracking-widest text-xs flex items-center gap-2 transition-all ${isLoading
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-amber-500 hover:bg-amber-400 text-black shadow-[0_0_20px_rgba(245,158,11,0.3)]'
                                }`}
                        >
                            {isLoading ? 'Training Neural Net...' : 'Run Simulation'}
                            {!isLoading && <Play className="w-4 h-4 fill-current" />}
                        </button>
                    </div>
                </div>
            </HUDCard>

            {/* Results Display */}
            {result && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in zoom-in-50 duration-500">
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Precision (Win Rate)</div>
                        <div className={`text-5xl font-black font-mono tracking-tighter ${result.precision > 0.7 ? 'text-emerald-400' : 'text-amber-400'}`}>
                            <ScrambleText text={(result.precision * 100).toFixed(1)} />%
                        </div>
                        <div className="mt-2 text-[10px] text-slate-500 font-bold bg-white/5 px-2 py-1 rounded">
                            target: 80.0%
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Total Signals</div>
                        <div className="text-4xl font-black text-white font-mono tracking-tighter">
                            <ScrambleText text={result.trade_count.toString()} />
                        </div>
                        <div className="mt-2 text-[10px] text-slate-500">
                            High Conviction Trades
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Model F1-Score</div>
                        <div className="text-4xl font-black text-indigo-400 font-mono tracking-tighter">
                            {(result.f1 * 100).toFixed(1)}
                        </div>
                        <div className="mt-2 text-[10px] text-slate-500">
                            Harmonic Mean
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Optimal Threshold</div>
                        <div className="text-4xl font-black text-purple-400 font-mono tracking-tighter">
                            {result.optimized_threshold.toFixed(2)}
                        </div>
                        <div className="mt-2 text-[10px] text-slate-500">
                            Confidence Cutoff
                        </div>
                    </div>

                    {/* Enhanced Metrics Row */}
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Model Accuracy</div>
                        <div className="text-3xl font-black text-cyan-400 font-mono tracking-tighter">
                            <ScrambleText text={(result.accuracy * 100).toFixed(1)} />%
                        </div>
                    </div>

                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">Recall (Sensitivity)</div>
                        <div className="text-3xl font-black text-pink-400 font-mono tracking-tighter">
                            <ScrambleText text={(result.recall * 100).toFixed(1)} />%
                        </div>
                    </div>

                    <div className="col-span-1 md:col-span-2 p-6 rounded-2xl bg-white/5 border border-white/10 flex flex-col items-center justify-center text-center">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-2">ROC - AUC Score</div>
                        <div className="text-3xl font-black text-emerald-400 font-mono tracking-tighter flex items-center gap-2">
                            <Activity className="w-5 h-5" />
                            <ScrambleText text={(result.roc_auc * 100).toFixed(1)} />
                        </div>
                    </div>

                    {/* Data Intelligence Card */}
                    <HUDCard title="DATA INTELLIGENCE & QUALITY METRICS" neonColor="cyan" className="col-span-1 md:col-span-2 lg:col-span-4">
                        <div className="p-6 grid grid-cols-1 md:grid-cols-4 gap-6">
                            <div className="flex flex-col gap-1 border-r border-white/5 pr-6">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Dataset Range</span>
                                <span className="text-xs font-mono text-white">{result.train_start} <span className="text-slate-600">→</span> {result.test_end}</span>
                                <span className="text-[10px] text-emerald-400 mt-1">{(result.train_records + result.test_records).toLocaleString()} Candles</span>
                            </div>

                            <div className="flex flex-col gap-1 border-r border-white/5 pr-6">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Data Coverage</span>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg font-mono font-black text-white">{result.data_coverage_pct}%</span>
                                    {result.data_coverage_pct > 99 ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : <AlertTriangle className="w-4 h-4 text-amber-500" />}
                                </div>
                                <span className="text-[10px] text-slate-500">Missing: {result.missing_values_pct}%</span>
                            </div>

                            <div className="flex flex-col gap-1 border-r border-white/5 pr-6">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Data Freshness</span>
                                <div className="flex items-center gap-2">
                                    <span className={`text-lg font-mono font-black ${getFreshnessColor(result.data_freshness_hours)}`}>
                                        {result.data_freshness_hours < 1 ? "< 1h ago" : `${result.data_freshness_hours}h ago`}
                                    </span>
                                </div>
                                <span className="text-[10px] text-slate-500">Last: {new Date(result.last_updated).toLocaleTimeString()}</span>
                            </div>

                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Data Source</span>
                                <span className="text-xs font-mono text-cyan-400 flex items-center gap-2">
                                    <Server className="w-3 h-3" />
                                    {modelType.includes('daily') ? 'Historicals (Primary)' : 'Broker API (Real-time)'}
                                </span>
                            </div>
                        </div>
                    </HUDCard>
                </div>
            )}
        </div>
    );
};

export default Backtest;
