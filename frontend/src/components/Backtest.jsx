import React, { useState } from 'react';
import {
    Activity, Play, Server, Database, TrendingUp,
    Shield, CheckCircle, AlertTriangle, Cpu, Target
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// BASE API URL
const API_URL = import.meta.env.VITE_API_URL || "";

const Backtest = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [modelType, setModelType] = useState('daily');
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

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* Control Panel */}
            <HUDCard title="NEURAL BACKTEST ENGINE" neonColor="amber">
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
                                12 YEARS DATA (10Y TRAIN / 2Y TEST)
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-4">
                        <select
                            value={modelType}
                            onChange={(e) => setModelType(e.target.value)}
                            className="bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-widest text-slate-300 focus:outline-none focus:border-amber-500/50"
                        >
                            <option value="daily">Daily Strategist (12 Years)</option>
                            <option value="intraday">Intraday Sniper (7 Days)</option>
                        </select>

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

                    {/* Data Split Info */}
                    <HUDCard title="DATA INTELLIGENCE" neonColor="cyan" className="col-span-1 md:col-span-2 lg:col-span-4">
                        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Training Period (10Y)</span>
                                <span className="text-sm font-mono text-white">{result.train_start} <span className="text-slate-600">to</span> {result.train_end}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Testing Period (2Y)</span>
                                <span className="text-sm font-mono text-emerald-400">{result.test_start} <span className="text-slate-600">to</span> {result.test_end}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] uppercase font-bold text-slate-500">Total Records Analyzed</span>
                                <span className="text-sm font-mono text-cyan-400">{result.total_records.toLocaleString()} Candles</span>
                            </div>
                        </div>
                    </HUDCard>
                </div>
            )}
        </div>
    );
};

export default Backtest;
