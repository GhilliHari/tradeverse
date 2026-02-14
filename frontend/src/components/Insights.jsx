import React, { useState, useEffect } from 'react';
import {
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
    Tooltip
} from 'recharts';
import {
    Zap, Globe, Activity, AlertTriangle, Wifi
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';
import BrainVisualizer from './BrainVisualizer';

// --- BANK NIFTY INTRADAY F&O INTELLIGENCE ---

const Insights = () => {
    const [mmiData, setMmiData] = useState(null);
    const [predictData, setPredictData] = useState(null);
    const [newsData, setNewsData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [mmiRes, predictRes] = await Promise.all([
                    fetch('/api/market/mmi'),
                    fetch('/api/ai/predict_hybrid?symbol=NSE:BANKNIFTY')
                ]);

                const mmi = await mmiRes.json();
                const predict = await predictRes.json();

                // Fetch News separately to not block critical data
                fetch('/api/news')
                    .then(res => res.json())
                    .then(data => setNewsData(data))
                    .catch(err => console.error("News fetch error", err));

                setMmiData(mmi);
                setPredictData(predict);
            } catch (error) {
                console.error("Error fetching Insights data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 30000); // Update every 30s
        return () => clearInterval(interval);
    }, []);

    // Map Backend MMI to Radar Chart
    const radarData = [
        { subject: 'COR Confidence', A: predictData?.confidence ?? 0, fullMark: 100 },
        { subject: 'Causal Strength', A: (predictData?.causal_strength ?? 0.5) * 100, fullMark: 100 },
        { subject: 'Component Lead', A: ((predictData?.structural?.component_score ?? 0) + 1) * 50, fullMark: 100 },
        { subject: 'PCR Skew', A: mmiData?.components?.pcr_score ?? 30, fullMark: 100 },
        { subject: 'OI Support', A: mmiData?.components?.volume_score ?? 90, fullMark: 100 },
        { subject: 'BN Momentum', A: mmiData?.components?.momentum_score ?? 45, fullMark: 100 },
    ];

    const thoughts = [
        {
            id: 1,
            time: 'LIVE',
            category: 'STRUCTURAL',
            text: `Component Alpha: ${predictData?.structural?.component_status ?? "NEUTRAL"}`,
            details: `HDFC + ICICI + KOTAK Leadership Score: ${predictData?.structural?.component_score?.toFixed(2) ?? "0.00"}. Significant weightage aligned with Index.`,
            impact: 'HIGH'
        },
        {
            id: 2,
            time: 'GEX',
            category: 'DECISION',
            text: `Liquidity Walls: ${predictData?.structural?.gex?.put_wall ?? "---"} | ${predictData?.structural?.gex?.call_wall ?? "---"}`,
            details: `Institutional Support @ ${predictData?.structural?.gex?.put_wall} and Resistance @ ${predictData?.structural?.gex?.call_wall}. Max Pain: ${predictData?.structural?.gex?.max_pain}.`,
            impact: 'HIGH'
        },
        {
            id: 3,
            time: 'COR',
            category: 'ANALYSIS',
            text: `Regime: ${predictData?.regime ?? "SCANNING"}`,
            details: `Market operating in ${predictData?.regime} mode. Causal strength is ${(predictData?.causal_strength ?? 0.5).toFixed(2)}.`,
            impact: 'MEDIUM'
        }
    ];

    const newsFeed = [
        {
            source: 'NSE Data Feed',
            title: 'FII Net Long positions increased by 12% in Index Futures',
            sentiment: 'BULLISH',
            score: '+0.75',
            time: '10 mins ago'
        },
        {
            source: 'Global Macro',
            title: 'US 10Y Bond Yield cools off to 4.5% - Banking positive',
            sentiment: 'BULLISH',
            score: '+0.5',
            time: '35 mins ago'
        },
        {
            source: 'VIX Alert',
            title: 'India VIX spikes > 15. Option Premiums expanding.',
            sentiment: 'BEARISH',
            score: '-0.6',
            time: '1 hour ago'
        }
    ];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">

            {/* Top Row: System Status & Regime */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

                {/* 1. Regime Radar */}
                <HUDCard title="F&O REGIME SCANNER" neonColor="purple" className="h-full">
                    <div className="h-full w-full pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
                        <div className="absolute top-[20%] right-[-10%] w-[200px] h-[200px] bg-purple-600/10 blur-[60px] rounded-full" />
                    </div>

                    <div className="relative h-full flex flex-col p-3 gap-1">
                        {/* Row 1: Visual Radar (Upper Area) */}
                        <div className="relative h-[50%] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="85%" data={radarData}>
                                    <PolarGrid stroke="#ffffff20" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 9, fontWeight: 'bold' }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar
                                        name="Current State"
                                        dataKey="A"
                                        stroke="#a855f7"
                                        strokeWidth={2}
                                        fill="#a855f7"
                                        fillOpacity={0.3}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333' }}
                                        itemStyle={{ color: '#a855f7' }}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Row 1.5: Confidence Progress Bar */}
                        <div className="px-1 mt-1">
                            <div className="flex justify-between items-center mb-0.5">
                                <span className="text-[7px] text-slate-500 font-black uppercase">Intelligence Confidence</span>
                                <span className={`text-[8px] font-mono font-bold ${predictData?.confidence >= 70 ? 'text-cyan-400' : 'text-slate-400'}`}>
                                    {predictData?.confidence?.toFixed(1) ?? "0.0"}%
                                </span>
                            </div>
                            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                                <div
                                    className={`h-full transition-all duration-1000 ${predictData?.confidence >= 70 ? 'bg-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.5)]' : 'bg-slate-600'}`}
                                    style={{ width: `${predictData?.confidence ?? 0}%` }}
                                />
                            </div>
                        </div>

                        {/* Row 2: Tactical Readout (Bottom Area) */}
                        <div className="flex flex-col justify-between flex-1 pb-1 pt-2">
                            {/* Combined Info Row */}
                            <div className="flex items-end justify-between border-b border-white/5 pb-2">
                                <div>
                                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Active Regime</span>
                                    <div className="text-xl font-black text-purple-400 leading-none mt-0.5">
                                        <ScrambleText text={predictData?.regime ?? "SCANNING..."} />
                                    </div>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <div className="flex gap-1.5">
                                        <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border ${predictData?.daily?.status === 'POSITIVE' || predictData?.daily?.status === 'BULLISH' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-red-500/30 text-red-400 bg-red-500/10'}`}>
                                            Sentiment: {predictData?.daily?.status ?? "WAIT"}
                                        </span>
                                        <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border ${predictData?.intraday?.status === 'BUY' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-slate-500/30 text-slate-400 bg-slate-500/10'}`}>
                                            Signal: {predictData?.intraday?.status ?? "WAIT"}
                                        </span>
                                    </div>
                                    <div className="text-[7px] font-mono text-slate-500 uppercase">
                                        Causal: {(predictData?.causal_strength ?? 0.5).toFixed(2)}
                                    </div>
                                </div>
                            </div>

                            {/* Key Levels - Single Row Grid for density */}
                            <div className="grid grid-cols-4 gap-1">
                                <div className="text-center">
                                    <div className="text-[8px] text-slate-500 uppercase font-black">Pivot</div>
                                    <div className="text-xs font-mono font-bold text-white">{predictData?.tactical?.pivot ?? "----"}</div>
                                </div>
                                <div className="text-center border-l border-white/5">
                                    <div className="text-[8px] text-slate-500 uppercase font-black">Res (R1)</div>
                                    <div className="text-xs font-mono font-bold text-red-300">{predictData?.tactical?.r1 ?? "----"}</div>
                                </div>
                                <div className="text-center border-l border-white/5">
                                    <div className="text-[8px] text-slate-500 uppercase font-black">RSI</div>
                                    <div className={`text-xs font-mono font-bold ${predictData?.tactical?.rsi > 70 ? 'text-red-400' : predictData?.tactical?.rsi < 30 ? 'text-emerald-400' : 'text-blue-300'}`}>
                                        {predictData?.tactical?.rsi ?? "--"}
                                    </div>
                                </div>
                                <div className="text-center border-l border-white/5">
                                    <div className="text-[8px] text-slate-500 uppercase font-black">ATR</div>
                                    <div className="text-xs font-mono font-bold text-amber-300">{predictData?.tactical?.atr ?? "--"}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </HUDCard>

                {/* 2. Neural Brain Visualizer (NEW) */}
                <BrainVisualizer
                    scores={predictData?.model_scores || {}}
                    className="col-span-2 h-full"
                />
            </div>

            {/* Bottom Row: Neural Thought Process */}
            <HUDCard title="CORTEX.AI / F&O STRATEGY LOGIC" neonColor="cyan" className="min-h-[400px]">
                <div className="p-6">
                    <div className="relative border-l border-cyan-500/20 ml-3 space-y-8">
                        {thoughts.map((thought, i) => (
                            <div key={thought.id} className="ml-6 relative group">
                                {/* Timeline Node */}
                                <div className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 border-black 
                                    ${thought.impact === 'HIGH' ? 'bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.6)]' : 'bg-slate-700 border-slate-600'} 
                                    transition-all duration-300 group-hover:scale-125 z-10`}></div>

                                <div className="flex flex-col md:flex-row md:items-start gap-4 p-4 rounded-xl bg-gradient-to-r from-cyan-900/10 to-transparent border border-cyan-500/10 hover:border-cyan-500/30 transition-all">
                                    <div className="flex-shrink-0 flex flex-col items-center gap-2 min-w-[80px]">
                                        <span className="text-xs font-mono text-cyan-400">{thought.time}</span>
                                        {thought.category === 'DECISION' && <Zap className="w-4 h-4 text-amber-400 animate-pulse" />}
                                        {thought.category === 'ANALYSIS' && <Activity className="w-4 h-4 text-purple-400" />}
                                        {thought.category === 'RISK' && <AlertTriangle className="w-4 h-4 text-red-400" />}
                                        {thought.category === 'SCAN' && <Wifi className="w-4 h-4 text-emerald-400" />}
                                    </div>

                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-widest ${thought.category === 'DECISION' ? 'bg-amber-500/20 text-amber-400' :
                                                thought.category === 'ANALYSIS' ? 'bg-purple-500/20 text-purple-400' :
                                                    'bg-slate-700 text-slate-300'
                                                }`}>
                                                {thought.category}
                                            </span>
                                        </div>
                                        <p className="text-sm font-bold text-white mb-1">{thought.text}</p>
                                        <p className="text-xs text-slate-400 font-mono leading-relaxed">{thought.details}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </HUDCard>
        </div>
    );
};

export default Insights;
