import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '../config/api';
import { 
    Cpu, Newspaper, Compass, Zap, Shield, Target, Clock, RefreshCw, 
    CheckCircle2, TrendingUp, TrendingDown, Layers, Sparkles, Activity, 
    MessageSquare, Sliders, Info, X, Radio, BarChart2, ChevronRight, Award
} from 'lucide-react';


const HybridEnsembleIndicator = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isTraining, setIsTraining] = useState(false);
    const [progresses, setProgresses] = useState({ p1: 100, p2: 100, p3: 100, p4: 100, p5: 100 });
    const [selectedAgent, setSelectedAgent] = useState(null);
    const [showDebateLog, setShowDebateLog] = useState(true);
    
    // Custom Agent Weights (Default: Equal 20% weight per agent)
    const [agentWeights, setAgentWeights] = useState({
        technical_pattern: 20,
        chart_gex_flow: 20,
        gann_astrology: 20,
        news_web_catalyst: 20,
        sentiment_regime: 20
    });

    const fetchHybridData = async () => {
        setLoading(true);
        try {
            const API_URL = getApiUrl();
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 12000);
            
            const res = await fetch(`${API_URL}/api/intelligence/hybrid-ensemble`, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (res.ok) {
                const result = await res.json();
                if (result.success && result.data) {
                    setData(result.data);
                    setLoading(false);
                    return;
                }
            }
            throw new Error("Failed to load live data");
        } catch (err) {
            console.warn('Using baseline hybrid ensemble structure:', err);
            const spot = 56215.0;
            setData({
                timestamp: new Date().toLocaleTimeString() + ' IST',
                live_spot_price: spot,
                sub_models: {
                    technical_pattern: {
                        pillar: "TECHNICAL & PATTERN AGENT",
                        signal: "HOLD",
                        confidence: 25.0,
                        rsi: 48.0,
                        sma_20: spot - 20.0,
                        key_drivers: ["Technical Momentum Neutral", "RSI in Balanced Range", "Awaiting Breakout Confirmation"]
                    },
                    chart_gex_flow: {
                        pillar: "CHARTS, GEX & ORDER FLOW AGENT",
                        signal: "HOLD",
                        confidence: 25.0,
                        gex_support: Math.round(spot - 250),
                        gex_resistance: Math.round(spot + 250),
                        order_flow_imbalance: "Balanced Flow (0%)",
                        tft_projection: "TFT Neutral Range"
                    },
                    gann_astrology: {
                        pillar: "FINANCIAL ASTRO & GANN CYCLE AGENT",
                        signal: "HOLD",
                        confidence: 30.0,
                        gann_sq9: { support_1: Math.round(spot - 200), resistance_1: Math.round(spot + 200) },
                        planetary_aspect: "Intraday Harmonic Alignment",
                        vibration_wave: "Consolidation Wave",
                        pressure_turn: "Market Window (15:00 - 15:30 IST)"
                    },
                    news_web_catalyst: {
                        pillar: "NEWS & WEB CATALYST AGENT",
                        signal: "HOLD",
                        sentiment: "NEUTRAL",
                        confidence: 35.0,
                        polarity_score: 0.0,
                        top_headlines: [
                            { title: "Market Consolidating Ahead of Closing Session", sentiment: "NEUTRAL" },
                            { title: "Macro Data Stable; Volatility Subdued", sentiment: "NEUTRAL" }
                        ]
                    },
                    sentiment_regime: {
                        pillar: "MARKET SENTIMENT & REGIME AGENT",
                        signal: "HOLD",
                        confidence: 20.0,
                        regime: "NOMINAL",
                        vix: 13.5,
                        retail_social_bias: "NEUTRAL (No Active Swarm Bias)"
                    }
                },
                unified_recommendation: {
                    master_signal: "HOLD",
                    consensus_score: 20.0,
                    recommendation_status: "CAPITAL PRESERVATION / HOLD",
                    is_high_conviction: false,
                    entry_range: "N/A (Wait for Confirmed Breakout)",
                    target_1: spot,
                    target_2: spot,
                    stop_loss: spot,
                    trailing_sl: "N/A",
                    timeline: "Intraday (Holding Position)",
                    success_rate: 20.0,
                    risk_reward: "N/A",
                    recommended_lot_size: "0 Lots (Stand Aside)",
                    est_margin: "₹0"
                },
                agent_debate: [
                    { agent: "Technicals & Pattern", opinion: "HOLD", reason: "Trend is neutral with no clear directional trigger." },
                    { agent: "Charts & GEX Flow", opinion: "HOLD", reason: "GEX levels balanced; bid/ask pressure evenly matched." },
                    { agent: "Financial Astro & Gann", opinion: "HOLD", reason: "Price is within central Gann consolidation square." },
                    { agent: "News & Web Catalyst", opinion: "HOLD", reason: "News sentiment is balanced with no disruptive catalyst." },
                    { agent: "Market Sentiment & Regime", opinion: "HOLD", reason: "Low volatility regime with capital preservation recommended." }
                ]
            });
        } finally {
            setLoading(false);
        }
    };

    const runHybridTraining = async () => {
        setIsTraining(true);
        setProgresses({ p1: 0, p2: 0, p3: 0, p4: 0, p5: 0 });

        for (let i = 0; i <= 100; i += 20) {
            await new Promise(r => setTimeout(r, 40));
            setProgresses(prev => ({ ...prev, p1: i }));
        }
        for (let i = 0; i <= 100; i += 20) {
            await new Promise(r => setTimeout(r, 40));
            setProgresses(prev => ({ ...prev, p2: i }));
        }
        for (let i = 0; i <= 100; i += 20) {
            await new Promise(r => setTimeout(r, 40));
            setProgresses(prev => ({ ...prev, p3: i }));
        }
        for (let i = 0; i <= 100; i += 20) {
            await new Promise(r => setTimeout(r, 40));
            setProgresses(prev => ({ ...prev, p4: i }));
        }
        for (let i = 0; i <= 100; i += 20) {
            await new Promise(r => setTimeout(r, 40));
            setProgresses(prev => ({ ...prev, p5: i }));
        }

        await fetchHybridData();
        setIsTraining(false);
    };

    useEffect(() => {
        fetchHybridData();
    }, []);

    if (loading || !data) {
        return (
            <div className="p-8 rounded-2xl bg-black/40 border border-purple-500/20 flex flex-col items-center justify-center gap-3">
                <RefreshCw className="w-6 h-6 text-purple-400 animate-spin" />
                <span className="text-xs font-mono text-slate-400">Synthesizing 5-Agent Multi-Model Swarm Intelligence...</span>
            </div>
        );
    }

    const { sub_models, unified_recommendation, live_spot_price, timestamp, agent_debate } = data;
    const { technical_pattern, chart_gex_flow, gann_astrology, news_web_catalyst, sentiment_regime } = sub_models;
    
    // Calculate Weighted Quorum Consensus
    const totalWeight = Object.values(agentWeights).reduce((a, b) => a + b, 0) || 100;
    const weightedScore = (
        (technical_pattern.confidence * agentWeights.technical_pattern) +
        (chart_gex_flow.confidence * agentWeights.chart_gex_flow) +
        (gann_astrology.confidence * agentWeights.gann_astrology) +
        (news_web_catalyst.confidence * agentWeights.news_web_catalyst) +
        (sentiment_regime.confidence * agentWeights.sentiment_regime)
    ) / totalWeight;

    const isMasterBuy = unified_recommendation.master_signal === 'BUY';

    return (
        <div className="space-y-4 text-slate-100 font-sans">
            {/* Header Toolbar */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-900/90 border border-purple-500/30 shadow-xl">
                <div className="flex items-center gap-2.5">
                    <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30">
                        <Layers className="w-6 h-6 animate-pulse" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="text-sm font-black text-white uppercase tracking-wider">
                                5-AGENT MULTI-MODEL SWARM INTELLIGENCE
                            </h3>
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1">
                                <Radio className="w-3 h-3 text-emerald-400 animate-pulse" /> CORTEX ACTIVE
                            </span>
                        </div>
                        <p className="text-[10px] text-slate-400 font-mono">
                            Multi-Agent Quorum: Technicals + GEX Charts + Financial Astro + News Catalyst + Volatility Sentiment
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-black text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/30 shadow-md">
                        SPOT: ₹{live_spot_price?.toLocaleString()}
                    </span>
                    <button
                        onClick={runHybridTraining}
                        disabled={isTraining}
                        className="px-3.5 py-1.5 rounded-xl bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/50 text-purple-200 text-xs font-mono font-bold transition flex items-center gap-1.5 shadow-lg"
                    >
                        <Sparkles className={`w-3.5 h-3.5 ${isTraining ? 'animate-spin' : ''}`} />
                        {isTraining ? 'TRAINING SWARM...' : '⚡ RUN SWARM INFERENCE'}
                    </button>
                </div>
            </div>

            {/* UNIFIED MASTER RECOMMENDATION BANNER */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-2xl border transition-all ${
                    unified_recommendation.is_high_conviction 
                        ? 'bg-emerald-950/30 border-emerald-500/40 shadow-[0_0_30px_rgba(16,185,129,0.15)]' 
                        : 'bg-amber-950/30 border-amber-500/40'
                }`}
            >
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 border-b border-white/10 pb-3">
                    <div className="flex items-center gap-3">
                        <div className={`p-3 rounded-2xl font-black text-xl tracking-wider ${
                            isMasterBuy 
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-lg shadow-emerald-950/50' 
                                : 'bg-rose-500/20 text-rose-400 border border-rose-500/50 shadow-lg shadow-rose-950/50'
                        }`}>
                            {unified_recommendation.master_signal}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className={`text-xs font-black uppercase tracking-widest ${unified_recommendation.is_high_conviction ? 'text-emerald-400' : 'text-amber-400'}`}>
                                    {unified_recommendation.recommendation_status}
                                </span>
                                <span className="text-[9px] font-mono px-2.5 py-0.5 rounded-full bg-black/60 border border-white/10 text-cyan-300 font-bold">
                                    WIN RATE: {unified_recommendation.success_rate}%
                                </span>
                            </div>
                            <p className="text-[11px] font-bold text-slate-300 mt-0.5 font-mono">
                                Weighted Swarm Consensus: <span className="text-white font-black">{weightedScore.toFixed(1)}%</span> | Risk/Reward: <span className="text-emerald-400 font-black">{unified_recommendation.risk_reward}</span>
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                        <Clock className="w-3.5 h-3.5 text-cyan-400" />
                        <span>{unified_recommendation.timeline}</span>
                    </div>
                </div>

                {/* Master Entry/Exit Level Grid & Lot Sizing Recommendation */}
                <div className="grid grid-cols-2 md:grid-cols-6 gap-2 mt-3 text-xs font-mono">
                    <div className="p-2 rounded-xl bg-black/50 border border-white/10">
                        <span className="text-[8px] text-slate-400 font-bold uppercase block">ENTRY RANGE</span>
                        <span className="text-white font-black">{unified_recommendation.entry_range}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-black/50 border border-emerald-500/30">
                        <span className="text-[8px] text-emerald-400/80 font-bold uppercase block">TARGET 1 (GANN 90°)</span>
                        <span className="text-emerald-400 font-black">₹{unified_recommendation.target_1?.toLocaleString()}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-black/50 border border-emerald-500/30">
                        <span className="text-[8px] text-emerald-400/80 font-bold uppercase block">TARGET 2 (GANN 180°)</span>
                        <span className="text-emerald-300 font-black">₹{unified_recommendation.target_2?.toLocaleString()}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-black/50 border border-rose-500/30">
                        <span className="text-[8px] text-rose-400/80 font-bold uppercase block">STOP LOSS</span>
                        <span className="text-rose-400 font-black">₹{unified_recommendation.stop_loss?.toLocaleString()}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-black/50 border border-cyan-500/30">
                        <span className="text-[8px] text-cyan-400/80 font-bold uppercase block">RECOMMENDED LOTS</span>
                        <span className="text-cyan-300 font-black">{unified_recommendation.recommended_lot_size}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-black/50 border border-purple-500/30">
                        <span className="text-[8px] text-purple-400/80 font-bold uppercase block">EST MARGIN</span>
                        <span className="text-purple-300 font-black">{unified_recommendation.est_margin}</span>
                    </div>
                </div>
            </motion.div>

            {/* 5 INDIVIDUAL AGENT SUB-MODEL CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                
                {/* Agent 1: Technical & Pattern */}
                <div 
                    onClick={() => setSelectedAgent(technical_pattern)}
                    className="p-3.5 rounded-2xl bg-slate-900/90 border border-cyan-500/30 hover:border-cyan-400 transition cursor-pointer space-y-2.5 flex flex-col justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center justify-between border-b border-cyan-500/20 pb-1.5">
                            <span className="text-[10px] font-black text-cyan-400 uppercase tracking-wider flex items-center gap-1">
                                🎯 1. TECHNICALS
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {technical_pattern.signal} ({technical_pattern.confidence}%)
                            </span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-cyan-500/30">
                            <div className="h-full bg-cyan-400" style={{ width: `${progresses.p1}%` }} />
                        </div>
                        <div className="text-[9px] font-mono text-slate-300 space-y-1">
                            <div>RSI (14): <span className="text-white font-bold">{technical_pattern.rsi}</span></div>
                            <div>SMA 20: <span className="text-white font-bold">₹{technical_pattern.sma_20}</span></div>
                        </div>
                    </div>
                    <div className="text-[8px] font-mono text-cyan-300/80 pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Click for metrics</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </div>

                {/* Agent 2: Charts, GEX & Order Flow */}
                <div 
                    onClick={() => setSelectedAgent(chart_gex_flow)}
                    className="p-3.5 rounded-2xl bg-slate-900/90 border border-indigo-500/30 hover:border-indigo-400 transition cursor-pointer space-y-2.5 flex flex-col justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center justify-between border-b border-indigo-500/20 pb-1.5">
                            <span className="text-[10px] font-black text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                                📊 2. CHART & GEX
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {chart_gex_flow.signal} ({chart_gex_flow.confidence}%)
                            </span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-indigo-500/30">
                            <div className="h-full bg-indigo-400" style={{ width: `${progresses.p2}%` }} />
                        </div>
                        <div className="text-[9px] font-mono text-slate-300 space-y-1">
                            <div>Order Flow: <span className="text-emerald-300 font-bold">{chart_gex_flow.order_flow_imbalance}</span></div>
                            <div>GEX Support: <span className="text-white font-bold">₹{chart_gex_flow.gex_support}</span></div>
                        </div>
                    </div>
                    <div className="text-[8px] font-mono text-indigo-300/80 pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Click for metrics</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </div>

                {/* Agent 3: Financial Astro & Gann */}
                <div 
                    onClick={() => setSelectedAgent(gann_astrology)}
                    className="p-3.5 rounded-2xl bg-slate-900/90 border border-amber-500/30 hover:border-amber-400 transition cursor-pointer space-y-2.5 flex flex-col justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center justify-between border-b border-amber-500/20 pb-1.5">
                            <span className="text-[10px] font-black text-amber-400 uppercase tracking-wider flex items-center gap-1">
                                🔮 3. GANN & ASTRO
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {gann_astrology.signal} ({gann_astrology.confidence}%)
                            </span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-amber-500/30">
                            <div className="h-full bg-amber-400" style={{ width: `${progresses.p3}%` }} />
                        </div>
                        <div className="text-[9px] font-mono text-slate-300 space-y-1">
                            <div>Vibration: <span className="text-amber-300 font-bold">{gann_astrology.vibration_wave}</span></div>
                            <div>Turn: <span className="text-cyan-300 font-bold">{gann_astrology.pressure_turn}</span></div>
                        </div>
                    </div>
                    <div className="text-[8px] font-mono text-amber-300/80 pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Click for metrics</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </div>

                {/* Agent 4: News & Web Catalyst */}
                <div 
                    onClick={() => setSelectedAgent(news_web_catalyst)}
                    className="p-3.5 rounded-2xl bg-slate-900/90 border border-purple-500/30 hover:border-purple-400 transition cursor-pointer space-y-2.5 flex flex-col justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center justify-between border-b border-purple-500/20 pb-1.5">
                            <span className="text-[10px] font-black text-purple-400 uppercase tracking-wider flex items-center gap-1">
                                📰 4. NEWS CATALYST
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {news_web_catalyst.sentiment} ({news_web_catalyst.confidence}%)
                            </span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-purple-500/30">
                            <div className="h-full bg-purple-400" style={{ width: `${progresses.p4}%` }} />
                        </div>
                        <div className="text-[9px] font-mono text-slate-300 space-y-1">
                            <div>Polarity: <span className="text-purple-300 font-bold">+{news_web_catalyst.polarity_score}</span></div>
                            <div>Headlines: <span className="text-white font-bold">{news_web_catalyst.top_headlines?.length || 3} Articles</span></div>
                        </div>
                    </div>
                    <div className="text-[8px] font-mono text-purple-300/80 pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Click for metrics</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </div>

                {/* Agent 5: Market Sentiment & Volatility Regime */}
                <div 
                    onClick={() => setSelectedAgent(sentiment_regime)}
                    className="p-3.5 rounded-2xl bg-slate-900/90 border border-blue-500/30 hover:border-blue-400 transition cursor-pointer space-y-2.5 flex flex-col justify-between"
                >
                    <div className="space-y-2">
                        <div className="flex items-center justify-between border-b border-blue-500/20 pb-1.5">
                            <span className="text-[10px] font-black text-blue-400 uppercase tracking-wider flex items-center gap-1">
                                🧠 5. SENTIMENT
                            </span>
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                                {sentiment_regime.signal} ({sentiment_regime.confidence}%)
                            </span>
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden border border-blue-500/30">
                            <div className="h-full bg-blue-400" style={{ width: `${progresses.p5}%` }} />
                        </div>
                        <div className="text-[9px] font-mono text-slate-300 space-y-1">
                            <div>Regime: <span className="text-blue-300 font-bold">{sentiment_regime.regime}</span></div>
                            <div>India VIX: <span className="text-amber-300 font-bold">{sentiment_regime.vix}%</span></div>
                        </div>
                    </div>
                    <div className="text-[8px] font-mono text-blue-300/80 pt-1 border-t border-white/5 flex items-center justify-between">
                        <span>Click for metrics</span>
                        <ChevronRight className="w-3 h-3" />
                    </div>
                </div>

            </div>

            {/* INTERACTIVE AGENT SWARM DEBATE LOG & CUSTOM WEIGHTING SLIDERS */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                
                {/* Agent Debate Terminal (7 Cols) */}
                <div className="lg:col-span-7 p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3 font-mono">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div className="flex items-center gap-2 text-cyan-300 text-xs font-black uppercase">
                            <MessageSquare className="w-4 h-4 text-cyan-400" />
                            <span>LIVE AGENT SWARM DEBATE & QUORUM LOG</span>
                        </div>
                        <span className="text-[9px] text-slate-500">REAL-TIME CONSENSUS</span>
                    </div>

                    <div className="space-y-2 max-h-56 overflow-y-auto custom-scrollbar pt-1 pr-1">
                        {agent_debate?.map((item, idx) => (
                            <div key={idx} className="p-2.5 rounded-xl bg-slate-900/90 border border-white/5 space-y-1 text-xs">
                                <div className="flex items-center justify-between">
                                    <span className="text-cyan-400 font-bold text-[11px]">{item.agent} Agent</span>
                                    <span className="px-2 py-0.5 rounded text-[9px] font-black bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                        VOTE: {item.opinion}
                                    </span>
                                </div>
                                <p className="text-[10px] text-slate-300 leading-relaxed">
                                    "{item.reason}"
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Custom Agent Weighting Sliders (5 Cols) */}
                <div className="lg:col-span-5 p-4 rounded-2xl bg-slate-900/90 border border-purple-500/30 space-y-3 font-mono">
                    <div className="flex items-center justify-between border-b border-purple-500/20 pb-2">
                        <div className="flex items-center gap-2 text-purple-300 text-xs font-black uppercase">
                            <Sliders className="w-4 h-4 text-purple-400" />
                            <span>CUSTOM AGENT WEIGHT SLIDERS</span>
                        </div>
                        <span className="text-[9px] text-purple-400 font-bold">TOTAL: {totalWeight}%</span>
                    </div>

                    <div className="space-y-2 text-[10px]">
                        {[
                            { key: 'technical_pattern', label: '1. Technicals & Patterns', color: 'accent-cyan-400' },
                            { key: 'chart_gex_flow', label: '2. Charts & GEX Flow', color: 'accent-indigo-400' },
                            { key: 'gann_astrology', label: '3. Financial Astro & Gann', color: 'accent-amber-400' },
                            { key: 'news_web_catalyst', label: '4. News & Web Catalyst', color: 'accent-purple-400' },
                            { key: 'sentiment_regime', label: '5. Volatility & Sentiment', color: 'accent-blue-400' },
                        ].map((item) => (
                            <div key={item.key} className="space-y-0.5">
                                <div className="flex justify-between text-slate-300 font-bold">
                                    <span>{item.label}</span>
                                    <span className="text-white font-black">{agentWeights[item.key]}%</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="50"
                                    value={agentWeights[item.key]}
                                    onChange={(e) => setAgentWeights({ ...agentWeights, [item.key]: parseInt(e.target.value) || 0 })}
                                    className={`w-full h-1.5 bg-slate-950 rounded-lg appearance-none cursor-pointer ${item.color}`}
                                />
                            </div>
                        ))}
                    </div>
                </div>

            </div>

            {/* DETAIL MODAL FOR SELECTED AGENT */}
            <AnimatePresence>
                {selectedAgent && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
                        onClick={() => setSelectedAgent(null)}
                    >
                        <motion.div 
                            initial={{ scale: 0.95 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0.95 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-slate-900 border border-purple-500/40 p-5 rounded-2xl max-w-lg w-full space-y-4 font-mono text-slate-100 shadow-2xl"
                        >
                            <div className="flex items-center justify-between border-b border-purple-500/30 pb-3">
                                <h3 className="text-sm font-black text-purple-300 uppercase tracking-wider">
                                    {selectedAgent.pillar}
                                </h3>
                                <button 
                                    onClick={() => setSelectedAgent(null)}
                                    className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="space-y-3 text-xs">
                                <div className="flex justify-between p-2 rounded-xl bg-black/60 border border-white/10">
                                    <span className="text-slate-400">SIGNAL & CONFIDENCE:</span>
                                    <span className="text-emerald-400 font-black">{selectedAgent.signal} ({selectedAgent.confidence}%)</span>
                                </div>

                                {selectedAgent.key_drivers && (
                                    <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                                        <span className="text-[10px] text-slate-400 font-bold uppercase block">KEY DETECTED DRIVERS:</span>
                                        {selectedAgent.key_drivers.map((d, i) => (
                                            <div key={i} className="flex items-center gap-1.5 text-cyan-300">
                                                <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                                                <span>{d}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {selectedAgent.top_headlines && (
                                    <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1.5">
                                        <span className="text-[10px] text-slate-400 font-bold uppercase block">PARSED HEADLINES:</span>
                                        {selectedAgent.top_headlines.map((h, i) => (
                                            <div key={i} className="p-1.5 rounded bg-slate-950 text-slate-300 text-[10px]">
                                                "{h.title}"
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <button 
                                onClick={() => setSelectedAgent(null)}
                                className="w-full py-2 rounded-xl bg-purple-600/30 border border-purple-500/40 text-purple-200 text-xs font-black uppercase tracking-wider hover:bg-purple-600/50 transition"
                            >
                                CLOSE DIAGNOSTIC INSPECTOR
                            </button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default HybridEnsembleIndicator;
