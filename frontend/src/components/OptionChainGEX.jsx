import React, { useState, useEffect } from 'react';
import {
    Shield, Brain, Zap, Maximize, Activity, AlertTriangle,
    TrendingUp, TrendingDown, Gauge, RefreshCw, Layers, Compass
} from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { workerSetInterval, workerClearInterval } from '../utils/workerTimer';
import { API_URL } from '../config/api';

const OptionChainGEX = ({ symbol = "NSE:BANKNIFTY" }) => {
    const [gexData, setGexData] = useState(null);
    const [chainData, setChainData] = useState([]);
    const [spot, setSpot] = useState(0);
    const [ivSurface, setIvSurface] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const token = localStorage.getItem('token');

    const getUrl = (path) => `${(API_URL || '').replace(/\/$/, '')}${path}`;

    const fetchGex = async () => {
        try {
            const res = await fetch(getUrl(`/api/market/gex/${symbol}`), {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'success') {
                    setGexData(data.analysis);
                    setChainData(data.chain || []);
                    setSpot(data.spot || 0);
                    setError(null);
                } else {
                    setError(data.detail);
                }
            } else {
                setError(`Server Error: ${res.status}`);
            }
        } catch (e) {
            console.error("GEX Fetch Error:", e);
            setError("Network Error: Could not reach backend.");
        } finally {
            setIsLoading(false);
        }
    };

    const fetchIvSurface = async () => {
        try {
            const res = await fetch(getUrl(`/api/market/iv_surface/${symbol}`));
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'success') {
                    setIvSurface(data.surface);
                }
            }
        } catch (e) {
            // silent fallback
        }
    };

    useEffect(() => {
        fetchGex();
        fetchIvSurface();
        const interval = workerSetInterval(() => {
            fetchGex();
            fetchIvSurface();
        }, 10000); // 10s refresh
        return () => workerClearInterval(interval);
    }, [symbol]);

    if (isLoading && !gexData) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500 font-mono">
                <Activity className="w-8 h-8 animate-pulse mb-4 text-indigo-400" />
                <p className="text-xs font-black uppercase tracking-widest">Scanning Volatility Surface & GEX Walls...</p>
            </div>
        );
    }

    if (!gexData || chainData.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500 font-mono">
                <Shield className="w-8 h-8 mb-4 opacity-50" />
                <p className="text-xs font-black uppercase tracking-widest">GEX Scanner Offline</p>
                <p className="text-[10px] mt-2 max-w-xs text-center text-red-400/70 font-bold uppercase tracking-tighter">
                    {error || "Option chain data is currently unavailable. The broker might be disconnected or rate-limited."}
                </p>
            </div>
        );
    }

    const maxOI = Math.max(
        ...chainData.map(c => Math.max(c.oi_ce || 0, c.oi_pe || 0)),
        1
    );

    const isLive = gexData.is_live;
    const isPositiveGamma = gexData.is_positive_gamma ?? (spot >= (gexData.zero_gamma_level || spot));
    const zeroGamma = gexData.zero_gamma_level || Math.round((gexData.call_wall + gexData.put_wall) / 2);
    const gammaDist = spot - zeroGamma;
    const isSqueezeActive = gexData.squeeze_alert && gexData.squeeze_alert !== 'STABLE_PINNED';

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 font-sans">
            {/* Real-time Gamma Squeeze Alert Banner */}
            {isSqueezeActive && (
                <div className={`p-4 rounded-2xl border flex items-center justify-between text-xs font-mono shadow-lg ${
                    gexData.squeeze_urgency === 'EXTREME'
                        ? 'bg-red-950/40 border-red-500/50 text-red-300 shadow-red-500/10'
                        : 'bg-amber-950/40 border-amber-500/50 text-amber-300 shadow-amber-500/10'
                }`}>
                    <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 animate-pulse text-amber-400 shrink-0" />
                        <div>
                            <span className="font-black uppercase tracking-wider block text-white">
                                {gexData.squeeze_alert?.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[11px] opacity-90">{gexData.squeeze_message}</span>
                        </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest bg-black/40 border border-white/10 shrink-0 ml-2">
                        {gexData.squeeze_urgency} URGENCY
                    </span>
                </div>
            )}

            {/* Header Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {/* Call Wall */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <Shield className="w-3 h-3 text-red-400" />
                        Call Wall
                    </p>
                    <p className="text-xl font-black text-white mt-1 font-mono">{gexData.call_wall}</p>
                    <p className="text-[9px] text-red-400 font-bold uppercase mt-0.5">Heavy Resistance</p>
                </div>

                {/* Put Wall */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <Shield className="w-3 h-3 text-emerald-400" />
                        Put Wall
                    </p>
                    <p className="text-xl font-black text-white mt-1 font-mono">{gexData.put_wall}</p>
                    <p className="text-[9px] text-emerald-400 font-bold uppercase mt-0.5">Heavy Support</p>
                </div>

                {/* Zero Gamma Level */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <Gauge className="w-3 h-3 text-cyan-400" />
                        Zero Gamma Flip
                    </p>
                    <p className="text-xl font-black text-cyan-300 mt-1 font-mono">₹{zeroGamma?.toLocaleString()}</p>
                    <p className="text-[9px] font-mono text-slate-400 mt-0.5">
                        Δ: <span className={gammaDist >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                            {gammaDist >= 0 ? `+${gammaDist.toFixed(0)}` : gammaDist.toFixed(0)} pts
                        </span>
                    </p>
                </div>

                {/* Gamma Regime */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <Activity className="w-3 h-3 text-purple-400" />
                        MM Gamma Regime
                    </p>
                    <div className="mt-1">
                        <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-black tracking-wider uppercase font-mono ${
                            isPositiveGamma
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                                : 'bg-red-500/20 text-red-300 border border-red-500/40'
                        }`}>
                            {isPositiveGamma ? 'POSITIVE GAMMA' : 'NEGATIVE GAMMA'}
                        </span>
                        <p className="text-[8px] text-slate-400 mt-1 truncate">
                            {isPositiveGamma ? 'Volatility Suppressed (Chop)' : 'Volatility Amplified (Trend)'}
                        </p>
                    </div>
                </div>

                {/* Max Pain */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        Max Pain
                    </p>
                    <p className="text-xl font-black text-amber-400 mt-1 font-mono">{gexData.max_pain}</p>
                    <p className="text-[9px] text-slate-400 mt-0.5">Expiry Magnet</p>
                </div>

                {/* PCR Sentiment */}
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-1.5">
                        <Brain className="w-3 h-3 text-indigo-400" />
                        PCR Sentiment
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                        <p className="text-xl font-black text-white font-mono">
                            {typeof gexData.pcr === 'number' ? gexData.pcr.toFixed(3) : gexData.pcr}
                        </p>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-black tracking-wider uppercase ${
                            gexData.sentiment === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' :
                            gexData.sentiment === 'BEARISH' ? 'bg-red-500/20 text-red-400' : 'bg-slate-500/20 text-slate-400'
                        }`}>
                            {gexData.sentiment}
                        </span>
                    </div>
                </div>
            </div>

            {/* VOLATILITY SMILE & SKEW SURFACE HUD */}
            {ivSurface && (
                <div className="glass-panel p-6 rounded-3xl border border-white/5 space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/5 pb-3">
                        <div className="flex items-center gap-2">
                            <Compass className="w-4 h-4 text-cyan-400" />
                            <h3 className="text-sm font-black text-white uppercase tracking-wider font-mono">
                                Implied Volatility (IV) Smile & Skew Surface
                            </h3>
                        </div>

                        {/* Directives and Skew Pills */}
                        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                            <div className="px-2.5 py-1 rounded-xl bg-slate-900 border border-white/10 flex items-center gap-1.5">
                                <span className="text-slate-500 text-[10px]">ATM IV:</span>
                                <span className="text-white font-bold">{ivSurface.atm_iv}%</span>
                            </div>
                            <div className="px-2.5 py-1 rounded-xl bg-slate-900 border border-white/10 flex items-center gap-1.5">
                                <span className="text-slate-500 text-[10px]">IV Rank:</span>
                                <span className="text-amber-300 font-bold">{ivSurface.iv_rank}%</span>
                            </div>
                            <div className="px-2.5 py-1 rounded-xl bg-slate-900 border border-white/10 flex items-center gap-1.5">
                                <span className="text-slate-500 text-[10px]">Skew:</span>
                                <span className={ivSurface.volatility_skew >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                                    {ivSurface.volatility_skew >= 0 ? `+${ivSurface.volatility_skew}` : ivSurface.volatility_skew}%
                                </span>
                            </div>
                            <div className="px-3 py-1 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 text-[10px] font-black uppercase">
                                {ivSurface.strategy_directive?.replace(/_/g, ' ')}
                            </div>
                        </div>
                    </div>

                    {/* Chart Container */}
                    <div className="h-56 w-full pt-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={ivSurface.surface_points} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="strike" stroke="#94a3b8" fontSize={10} fontStyle="mono" />
                                <YAxis stroke="#94a3b8" fontSize={10} unit="%" fontStyle="mono" domain={['auto', 'auto']} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#0c0d12',
                                        borderColor: '#ffffff20',
                                        borderRadius: '12px',
                                        fontSize: '11px',
                                        fontFamily: 'monospace'
                                    }}
                                />
                                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} />
                                <Line type="monotone" dataKey="ce_iv" name="Call IV (%)" stroke="#38bdf8" strokeWidth={2} dot={{ r: 2 }} />
                                <Line type="monotone" dataKey="pe_iv" name="Put IV (%)" stroke="#34d399" strokeWidth={2} dot={{ r: 2 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <p className="text-[10px] text-slate-400 font-mono italic">
                        💡 {ivSurface.skew_interpretation} — {ivSurface.directive_detail}
                    </p>
                </div>
            )}

            {/* Option Chain Geometry Ladder */}
            <div className="glass-panel p-6 rounded-3xl border border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Zap className="w-5 h-5 text-indigo-400" />
                        Option Chain Geometry
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">Spot: ₹{spot.toFixed(2)}</p>
                </div>

                {/* S1-R3 Ladder */}
                {(() => {
                    if (chainData.length === 0) return null;
                    const pivot = chainData.reduce((prev, curr) => 
                        Math.abs(curr.strike - spot) < Math.abs(prev.strike - spot) ? curr : prev
                    ).strike;

                    const strikeGap = chainData.length > 1 ? Math.abs(chainData[1].strike - chainData[0].strike) : 100;
                    const waveMag = strikeGap * 8; 

                    const rawR1 = spot + (waveMag * 0.382);
                    const rawR2 = spot + (waveMag * 0.618);
                    const rawR3 = spot + (waveMag * 1.000);
                    
                    const rawS1 = spot - (waveMag * 0.382);
                    const rawS2 = spot - (waveMag * 0.618);
                    const rawS3 = spot - (waveMag * 1.000);
                    
                    const snapToStrike = (target) => {
                        return chainData.reduce((prev, curr) => 
                            Math.abs(curr.strike - target) < Math.abs(prev.strike - target) ? curr : prev
                        ).strike;
                    };
                    
                    const sortedPE = [...chainData].sort((a,b) => b.oi_pe - a.oi_pe);
                    const sortedCE = [...chainData].sort((a,b) => b.oi_ce - a.oi_ce);
                    
                    const s1 = isLive ? (gexData.put_wall || sortedPE[0]?.strike) : snapToStrike(rawS1);
                    const s2 = snapToStrike(rawS2);
                    const s3 = snapToStrike(rawS3);
                    
                    const r1 = isLive ? (gexData.call_wall || sortedCE[0]?.strike) : snapToStrike(rawR1);
                    const r2 = snapToStrike(rawR2);
                    const r3 = snapToStrike(rawR3);
                    
                    return (
                        <div className="flex items-center justify-between px-6 py-4 bg-[#0c0d12]/50 rounded-2xl border border-white/5 mb-8 shadow-inner">
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">Wave C</span>
                                <span className="text-xs font-black text-emerald-500/70">{s3}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Wave 2</span>
                                <span className="text-sm font-black text-emerald-400">{s2}</span>
                            </div>
                            <div className="flex flex-col items-center relative group">
                                <div className="absolute -inset-2 bg-emerald-500/10 rounded-full blur-md" />
                                <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest relative">Base Support</span>
                                <span className="text-base font-black text-emerald-300 relative">{s1}</span>
                            </div>
                            
                            <div className="h-8 w-px bg-white/10" />
                            
                            <div className="flex flex-col items-center relative">
                                <div className="absolute -inset-2 bg-indigo-500/10 rounded-full blur-md" />
                                <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest flex items-center gap-1 relative">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" /> ATM PIVOT
                                </span>
                                <span className="text-xl font-black text-white relative">{pivot}</span>
                            </div>

                            <div className="h-8 w-px bg-white/10" />

                            <div className="flex flex-col items-center relative group">
                                <div className="absolute -inset-2 bg-red-500/10 rounded-full blur-md" />
                                <span className="text-[10px] font-black text-red-400 uppercase tracking-widest relative">Ceiling</span>
                                <span className="text-base font-black text-red-300 relative">{r1}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-red-500 uppercase tracking-widest">Wave 3</span>
                                <span className="text-sm font-black text-red-400">{r2}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-red-600 uppercase tracking-widest">Wave 5</span>
                                <span className="text-xs font-black text-red-500/70">{r3}</span>
                            </div>
                        </div>
                    );
                })()}

                {/* Table Header */}
                <div className="grid grid-cols-5 text-center mb-4 text-[10px] font-black uppercase text-slate-500 tracking-widest border-b border-white/5 pb-2">
                    <div className="col-span-2 text-red-400/70 pr-4 flex justify-end">Call OI (Resistance)</div>
                    <div className="text-white">Strike</div>
                    <div className="col-span-2 text-emerald-400/70 pl-4 flex justify-start">Put OI (Support)</div>
                </div>

                {/* Bars */}
                <div className="space-y-2">
                    {chainData.map((row, idx) => {
                        const callWidth = isLive ? (row.oi_ce / maxOI) * 100 : 0;
                        const putWidth = isLive ? (row.oi_pe / maxOI) * 100 : 0;
                        const isCallWall = row.strike === gexData.call_wall;
                        const isPutWall = row.strike === gexData.put_wall;
                        const isMaxPain = row.strike === gexData.max_pain;
                        const isZeroGamma = Math.abs(row.strike - zeroGamma) < 50;
                        const isSpotNear = Math.abs(spot - row.strike) <= 50;

                        return (
                            <div key={idx} className={`grid grid-cols-5 items-center ${isSpotNear ? 'bg-indigo-500/10 py-1 -mx-2 px-2 rounded-lg' : ''}`}>
                                {/* CE Side */}
                                <div className="col-span-2 flex items-center justify-end gap-3 pr-4 group">
                                    <span className="text-[10px] font-mono text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        ₹{(row.ce_premium || 0).toFixed(1)}
                                    </span>
                                    <span className="text-xs font-mono text-red-300 min-w-[50px] text-right">
                                        {isLive ? ((row.oi_ce || 0) / 1000).toFixed(1) + 'k' : '-'}
                                    </span>
                                    <div className="h-4 bg-slate-800 rounded-l-full w-full max-w-[150px] relative flex justify-end overflow-hidden">
                                        <div
                                            className={`h-full rounded-l-full transition-all duration-1000 ${isCallWall ? 'bg-red-500 shadow-[0_0_10px_#ef4444]' : 'bg-red-500/40'}`}
                                            style={{ width: `${Math.max(callWidth, 2)}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Strike */}
                                <div className="text-center relative">
                                    <span className={`text-sm font-black font-mono tracking-tight ${
                                        isCallWall ? 'text-red-400' : isPutWall ? 'text-emerald-400' : 'text-slate-300'
                                    }`}>
                                        {row.strike}
                                    </span>
                                    {isMaxPain && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[8px] text-amber-400 font-bold uppercase tracking-wider whitespace-nowrap">
                                            Max Pain
                                        </div>
                                    )}
                                    {isZeroGamma && !isMaxPain && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[8px] text-cyan-400 font-bold uppercase tracking-wider whitespace-nowrap">
                                            Zero Gamma
                                        </div>
                                    )}
                                </div>

                                {/* PE Side */}
                                <div className="col-span-2 flex items-center justify-start gap-3 pl-4 group">
                                    <div className="h-4 bg-slate-800 rounded-r-full w-full max-w-[150px] relative overflow-hidden">
                                        <div
                                            className={`h-full rounded-r-full transition-all duration-1000 ${isPutWall ? 'bg-emerald-500 shadow-[0_0_10px_#10b981]' : 'bg-emerald-500/40'}`}
                                            style={{ width: `${Math.max(putWidth, 2)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-mono text-emerald-300 min-w-[50px]">
                                        {isLive ? ((row.oi_pe || 0) / 1000).toFixed(1) + 'k' : '-'}
                                    </span>
                                    <span className="text-[10px] font-mono text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        ₹{(row.pe_premium || 0).toFixed(1)}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default OptionChainGEX;
