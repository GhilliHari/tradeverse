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
                    fetch('http://localhost:8000/api/market/mmi'),
                    fetch('http://localhost:8000/api/ai/predict_hybrid?symbol=NSE:BANKNIFTY')
                ]);

                const mmi = await mmiRes.json();
                const predict = await predictRes.json();

                // Fetch News separately to not block critical data
                fetch('http://localhost:8000/api/news')
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
        { subject: 'IV Rank', A: mmiData?.components?.vix_score ?? 75, fullMark: 100 },
        { subject: 'PCR Skew', A: mmiData?.components?.pcr_score ?? 30, fullMark: 100 },
        { subject: 'Gamma Risk', A: predictData?.regime === 'VOLATILE' ? 85 : 40, fullMark: 100 },
        { subject: 'Theta Decay', A: 60, fullMark: 100 },
        { subject: 'OI Support', A: mmiData?.components?.volume_score ?? 90, fullMark: 100 },
        { subject: 'BN Momentum', A: mmiData?.components?.momentum_score ?? 45, fullMark: 100 },
    ];

    const thoughts = [
        {
            id: 1,
            time: '1:45 PM',
            category: 'DECISION',
            text: 'Initiating Short Straddle @ 48,200.',
            details: 'IV Crush detected post-event. Combined Premium: ₹450. Targeting 30% decay by 3:00 PM.',
            impact: 'HIGH'
        },
        {
            id: 2,
            time: '1:30 PM',
            category: 'ANALYSIS',
            text: 'HDFC Bank VWAP Bullish Crossover.',
            details: 'HDFC Bank (Heavyweight) crossing VWAP with Volume. Expecting BN to test 48,350 resistance.',
            impact: 'MEDIUM'
        },
        {
            id: 3,
            time: '12:15 PM',
            category: 'RISK',
            text: 'Gamma Spike Warning (0DTE).',
            details: 'Approaching Expiry. 48,000 CE Delta shifted from 0.45 to 0.65 rapidly. Tightening Stop Loss.',
            impact: 'HIGH'
        },
        {
            id: 4,
            time: '11:00 AM',
            category: 'SCAN',
            text: 'OI Build-up detected at 47,500 PE.',
            details: 'Institutional Put writing observed (1.2M qty). Support floor effectively established.',
            impact: 'LOW'
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
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[300px]">

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

                        {/* Row 2: Tactical Readout (Bottom Area) */}
                        <div className="flex flex-col justify-between h-[50%] pb-1 pt-2">
                            {/* Combined Info Row */}
                            <div className="flex items-end justify-between border-b border-white/5 pb-2">
                                <div>
                                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Active Regime</span>
                                    <div className="text-xl font-black text-purple-400 leading-none mt-0.5">
                                        <ScrambleText text={predictData?.regime ?? "SCANNING..."} />
                                    </div>
                                </div>
                                <div className="flex gap-1.5 pb-0.5">
                                    <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border ${predictData?.daily?.status === 'BULLISH' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-red-500/30 text-red-400 bg-red-500/10'}`}>
                                        Daily: {predictData?.daily?.status ?? "WAIT"}
                                    </span>
                                    <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border ${predictData?.intraday?.status === 'BUY' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-slate-500/30 text-slate-400 bg-slate-500/10'}`}>
                                        Intra: {predictData?.intraday?.status ?? "WAIT"}
                                    </span>
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

                {/* 2. Global Sentiment Pulse */}
                <HUDCard title="MARKET SENTIMENT FEED" neonColor="pink" className="col-span-2 h-full">
                    <div className="p-4 h-full flex flex-col gap-2">
                        <div className="flex items-center justify-between pb-2 border-b border-white/10">
                            <div className="flex gap-4">
                                <div className="text-center">
                                    <div className="text-3xl font-black text-amber-400">
                                        {mmiData?.components?.vix_score ? (10 + (100 - mmiData.components.vix_score) / 5).toFixed(1) : "14.2"}
                                    </div>
                                    <div className="text-[10px] text-slate-500 font-bold uppercase">India VIX</div>
                                </div>
                                <div className="w-[1px] h-full bg-white/10 mx-2"></div>
                                <div className="text-center">
                                    <div className="text-3xl font-black text-white">
                                        {mmiData?.components?.pcr_score ? (mmiData.components.pcr_score / 100 + 0.5).toFixed(2) : "0.82"}
                                    </div>
                                    <div className="text-[10px] text-slate-500 font-bold uppercase">PCR (Bullish)</div>
                                </div>
                            </div>
                            <Globe className="w-12 h-12 text-slate-700 opacity-20" />
                        </div>

                        <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                            {(newsData.length > 0 ? newsData : newsFeed).map((news, i) => (
                                <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                                    <div className={`mt-1 w-2 h-2 rounded-full ${news.sentiment === 'BEARISH' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]'}`} />
                                    <div className="flex-1">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-[10px] font-bold text-pink-400 uppercase tracking-wider">{news.source || 'Market Feed'}</span>
                                            <span className="text-[10px] text-slate-500">{news.time || 'Just now'}</span>
                                        </div>
                                        <h4 className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">{news.title}</h4>
                                        {news.snippet && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{news.snippet}</p>}
                                    </div>
                                    {news.score && (
                                        <div className={`px-2 py-1 rounded text-[10px] font-black ${news.score.startsWith('+') ? 'bg-emerald-500/20 text-emerald-400' : news.score.startsWith('-') ? 'bg-red-500/20 text-red-400' : 'bg-slate-500/20 text-slate-400'}`}>
                                            {news.score}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </HUDCard>
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
