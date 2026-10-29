import React, { useState, useEffect } from 'react';
import { Shield, Brain, Zap, Maximize, Activity, AlertTriangle } from 'lucide-react';
import { workerSetInterval, workerClearInterval } from '../utils/workerTimer';

const getApiUrl = () => {
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved) return saved.replace(/\/$/, '');
    } catch (e) { }
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};
const API_URL = getApiUrl();

const OptionChainGEX = ({ symbol = "NSE:BANKNIFTY" }) => {
    const [gexData, setGexData] = useState(null);
    const [chainData, setChainData] = useState([]);
    const [spot, setSpot] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const token = localStorage.getItem('token');


    const fetchGex = async () => {
        try {
            const res = await fetch(`${API_URL}/api/market/gex/${symbol}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.status === 'success') {
                    setGexData(data.analysis);
                    setChainData(data.chain);
                    setSpot(data.spot);
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

    useEffect(() => {
        fetchGex();
        const interval = workerSetInterval(fetchGex, 10000); // refresh every 10s
        return () => workerClearInterval(interval);
    }, [symbol]);

    if (isLoading && !gexData) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500">
                <Activity className="w-8 h-8 animate-pulse mb-4" />
                <p className="text-xs font-black uppercase tracking-widest">Scanning Gamma Exposure...</p>
            </div>
        );
    }

    if (!gexData || chainData.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500">
                <Shield className="w-8 h-8 mb-4 opacity-50" />
                <p className="text-xs font-black uppercase tracking-widest">GEX Scanner Offline</p>
                <p className="text-[10px] mt-2 max-w-xs text-center text-red-400/70 font-bold uppercase tracking-tighter">
                    {error || "Option chain data is currently unavailable. The broker might be disconnected or rate-limited."}
                </p>
                {error && error.includes("initialization") && (
                    <p className="text-[8px] mt-1 text-slate-500 animate-pulse">Wait 10-20 seconds for neural layers to sync...</p>
                )}
            </div>
        );
    }


    // Find the max OI to scale the bars
    const maxOI = Math.max(
        ...chainData.map(c => Math.max(c.oi_ce, c.oi_pe)),
        1 // Default
    );

    const isLive = gexData.is_live;

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                        <Shield className="w-3 h-3 text-red-400" />
                        Call Wall (Resistance)
                    </p>
                    <p className="text-2xl font-black text-white mt-1">{gexData.call_wall}</p>
                    {isLive && <p className="text-[10px] text-red-400 font-bold">Massive CE Writing</p>}
                </div>
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-emerald-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                        <Shield className="w-3 h-3 text-emerald-400" />
                        Put Wall (Support)
                    </p>
                    <p className="text-2xl font-black text-white mt-1">{gexData.put_wall}</p>
                    {isLive && <p className="text-[10px] text-emerald-400 font-bold">Massive PE Writing</p>}
                </div>
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-16 h-16 bg-amber-500/10 blur-[20px] rounded-full -mr-8 -mt-8" />
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        Max Pain
                    </p>
                    <p className="text-2xl font-black text-amber-500 mt-1">{gexData.max_pain}</p>
                </div>
                <div className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
                    <p className="text-[9px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                        <Brain className="w-3 h-3 text-purple-400" />
                        PCR Sentiment
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                        <p className="text-2xl font-black text-white">{gexData.pcr}</p>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-black tracking-wider uppercase
                            ${gexData.sentiment === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' :
                                gexData.sentiment === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                                    'bg-slate-500/20 text-slate-400'}`}>
                            {gexData.sentiment}
                        </span>
                    </div>
                </div>
            </div>

            {/* True Market Data Warning */}
            {!isLive && (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 flex items-center gap-4">
                    <Activity className="w-6 h-6 text-amber-400 animate-pulse" />
                    <div>
                        <p className="text-sm font-black text-amber-400 uppercase tracking-widest">Mock Mode Warning</p>
                        <p className="text-xs text-amber-400/80 mt-1">
                            The API is currently returning 0 Open Interest. GEX logic is defaulting to strict mathematical approximations rather than live institutional data.
                        </p>
                    </div>
                </div>
            )}

            {/* Visualizer */}
            <div className="glass-panel p-6 rounded-3xl border border-white/5">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-lg font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Zap className="w-5 h-5 text-indigo-400" />
                        Option Chain Geometry
                    </h3>
                    <p className="text-xs text-slate-400 font-mono">Spot: ₹{spot.toFixed(2)}</p>
                </div>

                {/* Extended S1-R3 Ladder */}
                {(() => {
                    if (chainData.length === 0) return null;
                    
                    const pivot = chainData.reduce((prev, curr) => 
                        Math.abs(curr.strike - spot) < Math.abs(prev.strike - spot) ? curr : prev
                    ).strike;

                    // --- NEURAL ELLIOT WAVE GEOMETRY ENGINE ---
                    const strikeGap = chainData.length > 1 ? Math.abs(chainData[1].strike - chainData[0].strike) : 100;
                    const isLive = gexData.is_live;
                    
                    // Elliot Wave magnitude proxy: Assuming an Initial Impulse Wave (Wave 1) of 8x the strike gap
                    // (Using 8 as an idealized Fibonacci motive constraint)
                    const waveMag = strikeGap * 8; 
                    
                    // Pure continuous mathematical Elliot-Fibonacci levels relative to Spot price
                    const rawR1 = spot + (waveMag * 0.382);  // Wave 3 conservative (initial target)
                    const rawR2 = spot + (waveMag * 0.618);  // Wave 3 Golden Ratio extension
                    const rawR3 = spot + (waveMag * 1.000);  // Wave 5 extended exhaustion target
                    
                    const rawS1 = spot - (waveMag * 0.382);  // Wave 2 shallow retracement
                    const rawS2 = spot - (waveMag * 0.618);  // Wave 2 Golden retracement / Wave A
                    const rawS3 = spot - (waveMag * 1.000);  // Deep Wave C algorithmic flush
                    
                    // AI snapping logic: Lock abstract Fib targets to perfectly real, tradable Option Strikes
                    const snapToStrike = (target) => {
                        return chainData.reduce((prev, curr) => 
                            Math.abs(curr.strike - target) < Math.abs(prev.strike - target) ? curr : prev
                        ).strike;
                    };
                    
                    const sortedPE = [...chainData].sort((a,b) => b.oi_pe - a.oi_pe);
                    const sortedCE = [...chainData].sort((a,b) => b.oi_ce - a.oi_ce);
                    
                    // In Live Mode, the primary Base Support/Resistance still relies heavily on raw Institutional GEX (OI Walls).
                    // In Mock Mode, entirely pure Elliot waves are drafted. Secondary targets are ALWAYS wave-derived.
                    const s1 = isLive ? (gexData.put_wall || sortedPE[0]?.strike) : snapToStrike(rawS1);
                    const s2 = snapToStrike(rawS2);
                    const s3 = snapToStrike(rawS3);
                    
                    const r1 = isLive ? (gexData.call_wall || sortedCE[0]?.strike) : snapToStrike(rawR1);
                    const r2 = snapToStrike(rawR2);
                    const r3 = snapToStrike(rawR3);
                    
                    return (
                        <div className="flex items-center justify-between px-6 py-4 bg-[#0c0d12]/50 rounded-2xl border border-white/5 mb-8 shadow-inner">
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">Wave C (1.0)</span>
                                <span className="text-xs font-black text-emerald-500/70">{s3}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">Wave 2 (0.618)</span>
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
                                <span className="text-[10px] font-black text-red-400 uppercase tracking-widest relative">Ceiling (0.382)</span>
                                <span className="text-base font-black text-red-300 relative">{r1}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-red-500 uppercase tracking-widest">Wave 3 (0.618)</span>
                                <span className="text-sm font-black text-red-400">{r2}</span>
                            </div>
                            <div className="flex flex-col items-center">
                                <span className="text-[9px] font-black text-red-600 uppercase tracking-widest">Wave 5 (1.0)</span>
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
                        const isSpotNear = Math.abs(spot - row.strike) <= 50;

                        return (
                            <div key={idx} className={`grid grid-cols-5 items-center ${isSpotNear ? 'bg-indigo-500/10 py-1 -mx-2 px-2 rounded-lg' : ''}`}>
                                {/* CE Side */}
                                <div className="col-span-2 flex items-center justify-end gap-3 pr-4 group">
                                    <span className="text-[10px] font-mono text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        ₹{row.ce_premium.toFixed(1)}
                                    </span>
                                    <span className="text-xs font-mono text-red-300 min-w-[50px] text-right">
                                        {isLive ? (row.oi_ce / 1000).toFixed(1) + 'k' : '-'}
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
                                    <span className={`text-sm font-black font-mono tracking-tight ${isCallWall ? 'text-red-400' : isPutWall ? 'text-emerald-400' : 'text-slate-300'}`}>
                                        {row.strike}
                                    </span>
                                    {isMaxPain && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[8px] text-amber-400 font-bold uppercase tracking-wider whitespace-nowrap">
                                            Max Pain
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
                                        {isLive ? (row.oi_pe / 1000).toFixed(1) + 'k' : '-'}
                                    </span>
                                    <span className="text-[10px] font-mono text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        ₹{row.pe_premium.toFixed(1)}
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
