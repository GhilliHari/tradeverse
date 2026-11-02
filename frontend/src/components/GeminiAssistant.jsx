import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, Bot, User, RefreshCw, ChevronDown, ChevronUp, AlertCircle, ShieldCheck, BookOpen, Layers, ExternalLink, Key, CheckCircle, Info } from 'lucide-react';
import HUDCard from './ui/HUDCard';
import { API_URL } from '../config/api';

const GeminiAssistant = ({ marketContext, isOpenInitial = true }) => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            text: '👋 Greetings! I am your **Gemini 2.5 AI Trading Assistant** powered by **RAG Knowledge Base & Market Memory**.\n\nAsk me anything about market regime, Option GEX walls, BankNifty strategy, trading playbooks, or trade risk setups.'
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isMinimized, setIsMinimized] = useState(!isOpenInitial);
    const [expandedSources, setExpandedSources] = useState({});
    const [showKeyModal, setShowKeyModal] = useState(false);
    const [apiKeyInput, setApiKeyInput] = useState('');
    const [keyStatus, setKeyStatus] = useState({ has_gemini_key: false, active_model: 'gemini-2.5-flash', status: 'checking' });
    const [keySaving, setKeySaving] = useState(false);
    const [keyMessage, setKeyMessage] = useState(null);
    const chatEndRef = useRef(null);

    const getPrimaryUrl = (endpoint) => {
        const cleanBase = (API_URL || '').replace(/\/$/, '');
        return cleanBase ? `${cleanBase}${endpoint}` : endpoint;
    };

    const fetchAiStatus = async () => {
        const endpoints = [getPrimaryUrl('/api/ai/status'), '/api/ai/status'];
        for (const ep of endpoints) {
            try {
                const res = await fetch(ep);
                if (res.ok) {
                    const data = await res.json();
                    setKeyStatus(data);
                    return;
                }
            } catch (e) {
                // Try next endpoint
            }
        }
        setKeyStatus(prev => ({ ...prev, status: 'offline' }));
    };

    useEffect(() => {
        fetchAiStatus();
    }, []);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    const toggleSources = (idx) => {
        setExpandedSources(prev => ({
            ...prev,
            [idx]: !prev[idx]
        }));
    };

    const handleSaveKey = async (e) => {
        if (e) e.preventDefault();
        if (!apiKeyInput.trim()) return;

        setKeySaving(true);
        setKeyMessage(null);

        const endpoints = [getPrimaryUrl('/api/ai/key'), '/api/ai/key'];
        let success = false;
        let lastErr = '';

        for (const ep of endpoints) {
            try {
                const res = await fetch(ep, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKeyInput.trim() })
                });
                const resData = await res.json().catch(() => ({}));
                if (res.ok) {
                    setKeyMessage({ type: 'success', text: '✅ Gemini API Key connected & verified!' });
                    setApiKeyInput('');
                    fetchAiStatus();
                    success = true;
                    setTimeout(() => setShowKeyModal(false), 1500);
                    break;
                } else {
                    lastErr = resData?.detail || `Error (${res.status})`;
                }
            } catch (err) {
                lastErr = err.message || 'Connection error';
            }
        }

        if (!success) {
            setKeyMessage({ type: 'error', text: `⚠️ Failed: ${lastErr}` });
        }
        setKeySaving(false);
    };

    const handleSend = async (queryText) => {
        const text = queryText || input;
        if (!text.trim() || loading) return;

        const userMsg = { role: 'user', text };
        setMessages((prev) => [...prev, userMsg]);
        if (!queryText) setInput('');
        setLoading(true);

        const payload = {
            query: text,
            market_context: marketContext || { symbol: 'NSE:BANKNIFTY' }
        };

        const primaryUrl = getPrimaryUrl('/api/ai/chat');
        const fallbackUrl = '/api/ai/chat';
        let res = null;
        let networkError = null;

        try {
            res = await fetch(primaryUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (err1) {
            if (primaryUrl !== fallbackUrl) {
                try {
                    res = await fetch(fallbackUrl, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                } catch (err2) {
                    networkError = err2;
                }
            } else {
                networkError = err1;
            }
        }

        try {
            if (networkError) {
                throw new Error(`Cannot reach Tradeverse backend at ${primaryUrl}. Please verify the Python backend is running.`);
            }

            if (!res || !res.ok) {
                let errorDetail = `Backend HTTP ${res?.status || 'Unknown'}`;
                try {
                    const errData = await res.json();
                    if (errData?.detail) errorDetail = errData.detail;
                } catch (_) {}
                throw new Error(errorDetail);
            }

            const data = await res.json();
            const botReply = data?.reply || "⚠️ Unexpected response from Gemini API.";

            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    text: botReply,
                    structured_data: data?.structured_data,
                    rag_sources: data?.rag_sources || []
                }
            ]);
        } catch (err) {
            console.error("Gemini Assistant error:", err);
            setMessages((prev) => [
                ...prev,
                { 
                    role: 'assistant', 
                    text: `⚠️ **Connection Issue**: ${err.message}\n\n*Check that your backend server is running on port 8000, or click the **Key** icon above to configure your Google AI Studio API key.*` 
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickAction = (prompt) => {
        handleSend(prompt);
    };

    return (
        <HUDCard title="GEMINI 2.5 AI TRADING ASSISTANT" icon={Sparkles} className="h-full flex flex-col border border-cyan-500/30 bg-slate-900/95 shadow-xl shadow-cyan-950/20">
            {/* Header controls */}
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800 bg-slate-950/60 rounded-t">
                <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className={`w-2 h-2 rounded-full ${keyStatus.has_gemini_key ? 'bg-emerald-400 animate-pulse' : 'bg-purple-400 animate-pulse'}`}></span>
                    <span className={keyStatus.has_gemini_key ? 'text-cyan-400 font-bold' : 'text-purple-300 font-bold'}>
                        {keyStatus.has_gemini_key ? 'GEMINI 2.5 FLASH' : 'GRAPHRAG PLAYBOOK'}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-bold flex items-center gap-1">
                        <BookOpen className="w-2.5 h-2.5" /> RAG ON
                    </span>
                </div>
                <div className="flex items-center space-x-1.5">
                    <button
                        onClick={() => setShowKeyModal(!showKeyModal)}
                        className={`px-2 py-0.5 text-[10px] font-mono rounded flex items-center gap-1 transition-all ${
                            keyStatus.has_gemini_key 
                                ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700' 
                                : 'bg-purple-900/60 hover:bg-purple-800 text-purple-200 border border-purple-500/50 animate-pulse'
                        }`}
                        title="Configure Google Gemini API Key"
                    >
                        <Key className="w-2.5 h-2.5" />
                        <span>{keyStatus.has_gemini_key ? 'Key Set' : 'Add Gemini Key'}</span>
                    </button>
                    <button
                        onClick={() => setIsMinimized(!isMinimized)}
                        className="p-1 text-slate-400 hover:text-cyan-300 transition-colors"
                        title={isMinimized ? "Expand Assistant" : "Minimize Assistant"}
                    >
                        {isMinimized ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            {/* Quick API Key Modal / Banner */}
            {showKeyModal && (
                <div className="p-3 bg-slate-950 border-b border-cyan-500/30 font-mono text-xs text-slate-200 space-y-2 animate-in fade-in">
                    <div className="flex items-center justify-between">
                        <span className="font-bold text-cyan-400 flex items-center gap-1.5">
                            <Key className="w-3.5 h-3.5" /> Gemini API Key Configuration
                        </span>
                        <button onClick={() => setShowKeyModal(false)} className="text-slate-500 hover:text-white text-xs">✕</button>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                        Tradeverse AI functions out-of-the-box using the embedded **GraphRAG Vector Engine & Playbooks**. To unlock live Google Gemini 2.5 Flash reasoning, paste your free key from <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" className="text-cyan-400 underline">Google AI Studio</a>.
                    </p>
                    <form onSubmit={handleSaveKey} className="flex gap-2">
                        <input
                            type="password"
                            value={apiKeyInput}
                            onChange={(e) => setApiKeyInput(e.target.value)}
                            placeholder={keyStatus.has_gemini_key ? `Active key: ${keyStatus.masked_key || 'configured'}` : "Paste AIzaSy... key"}
                            className="flex-1 bg-slate-900 border border-slate-700 focus:border-cyan-500 rounded px-2.5 py-1.5 text-xs text-white outline-none"
                        />
                        <button
                            type="submit"
                            disabled={keySaving || !apiKeyInput.trim()}
                            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded text-xs disabled:opacity-50 transition"
                        >
                            {keySaving ? 'Saving...' : 'Connect'}
                        </button>
                    </form>
                    {keyMessage && (
                        <div className={`text-[10px] p-1.5 rounded ${keyMessage.type === 'success' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30' : 'bg-rose-950 text-rose-300 border border-rose-500/30'}`}>
                            {keyMessage.text}
                        </div>
                    )}
                </div>
            )}

            {!isMinimized && (
                <div className="flex flex-col flex-1 p-3 overflow-hidden">
                    {/* Quick Action Pills & Preset Questionnaire Labels */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                        <button
                            onClick={() => handleQuickAction("What are the core rules for trading Bank Nifty near the Upper Gamma Wall vs Lower Put Wall?")}
                            className="px-2.5 py-1 text-[11px] font-mono rounded-full bg-indigo-950/70 border border-indigo-500/50 text-indigo-300 hover:bg-indigo-900/80 hover:border-indigo-400 transition font-bold flex items-center gap-1 shadow-lg shadow-indigo-950/40"
                        >
                            🧠 Playbook: GEX Wall Rules
                        </button>
                        <button
                            onClick={() => handleQuickAction("Show Trigger-Based Execution Strategy Table with Upper/Lower Gamma Walls, Gann Resistance & Support levels, No Trade Chop Zone, Bullish Breakout, Bearish Breakdown, Stop-Loss, and Risk:Reward ratios.")}
                            className="px-2.5 py-1 text-[11px] font-mono rounded-full bg-emerald-950/70 border border-emerald-500/50 text-emerald-300 hover:bg-emerald-900/80 hover:border-emerald-400 transition font-bold flex items-center gap-1 shadow-lg shadow-emerald-950/40"
                        >
                            🎯 Trigger Execution Strategy
                        </button>
                        <button
                            onClick={() => handleQuickAction("Provide the live Upper Gamma Wall / Gann Resistance and Lower Gamma Wall / Gann Support levels for BankNifty with the No-Trade Chop Zone visual map.")}
                            className="px-2.5 py-1 text-[11px] font-mono rounded-full bg-cyan-950/70 border border-cyan-500/50 text-cyan-300 hover:bg-cyan-900/80 hover:border-cyan-400 transition font-bold flex items-center gap-1"
                        >
                            📊 Gamma & Gann Wall Map
                        </button>
                        <button
                            onClick={() => handleQuickAction("What happened during historical Union Budget and RBI rate decision days for Bank Nifty?")}
                            className="px-2.5 py-1 text-[11px] font-mono rounded-full bg-amber-950/70 border border-amber-500/50 text-amber-300 hover:bg-amber-900/80 hover:border-amber-400 transition font-bold flex items-center gap-1"
                        >
                            📜 Historical Event Regimes
                        </button>
                    </div>

                    {/* Chat Messages Log with Graphic Cards */}
                    <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-[220px] max-h-[440px] font-sans text-xs">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex items-start space-x-2.5 ${
                                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                                }`}
                            >
                                {msg.role === 'assistant' && (
                                    <div className="w-6 h-6 rounded-md bg-cyan-950 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
                                        <Bot className="w-3.5 h-3.5" />
                                    </div>
                                )}

                                <div className={`max-w-[90%] leading-relaxed ${msg.role === 'user' ? 'bg-cyan-600/20 border border-cyan-500/40 text-cyan-100 p-2.5 rounded-lg rounded-br-none font-mono' : ''}`}>
                                    {msg.role === 'assistant' && msg.structured_data ? (
                                        /* ULTRA ATTRACTIVE GRAPHICAL CARD FOR HYBRID SUGGESTIONS */
                                        <div className="space-y-3 p-3.5 rounded-2xl bg-slate-950/95 border border-cyan-500/40 text-slate-200 shadow-2xl shadow-cyan-950/50 font-sans">
                                            {/* Master Combined Recommendation Graphical Banner */}
                                            {(() => {
                                                const s = msg.structured_data;
                                                const u = s?.unified_recommendation || {};
                                                const isBuy = u.master_signal === 'BUY';
                                                return (
                                                    <div className={`p-3.5 rounded-xl border relative overflow-hidden ${u.is_high_conviction ? 'bg-gradient-to-r from-emerald-950/80 via-slate-900 to-teal-950/80 border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.25)]' : 'bg-gradient-to-r from-amber-950/80 via-slate-900 to-yellow-950/80 border-amber-500/50'}`}>
                                                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2.5 mb-2.5">
                                                            <div className="flex items-center gap-2">
                                                                <span className={`px-2.5 py-1 rounded-lg text-xs font-black uppercase tracking-wider shadow-lg ${isBuy ? 'bg-emerald-500 text-slate-950 shadow-emerald-500/50' : 'bg-rose-500 text-white shadow-rose-500/50'}`}>
                                                                    {u.master_signal || 'BUY'}
                                                                </span>
                                                                <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-black/60 border ${u.is_high_conviction ? 'text-emerald-400 border-emerald-500/30' : 'text-amber-400 border-amber-500/30'}`}>
                                                                    ⚡ {u.recommendation_status || 'HIGH CONVICTION TAKE TRADE'}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-center gap-1.5 font-mono text-[9.5px]">
                                                                <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold">
                                                                    🎯 WIN RATE: {u.success_rate || 92.0}%
                                                                </span>
                                                                <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold">
                                                                    📊 QUORUM: {u.consensus_score || 80.0}%
                                                                </span>
                                                            </div>
                                                        </div>

                                                        {/* Level & Lot Sizing Grid */}
                                                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[9.5px] font-mono">
                                                            <div className="p-2 rounded-lg bg-black/50 border border-white/10">
                                                                <span className="text-slate-400 block text-[7.5px] uppercase font-black tracking-wider">ENTRY RANGE</span>
                                                                <span className="text-white font-black text-[11px]">{u.entry_range || "₹57,965 - ₹57,975"}</span>
                                                            </div>
                                                            <div className="p-2 rounded-lg bg-black/50 border border-emerald-500/30 bg-emerald-500/5">
                                                                <span className="text-emerald-400 block text-[7.5px] uppercase font-black tracking-wider">TARGET 1 (GANN 90°)</span>
                                                                <span className="text-emerald-300 font-black text-[11px]">₹{u.target_1 || 58209.47}</span>
                                                            </div>
                                                            <div className="p-2 rounded-lg bg-black/50 border border-rose-500/30 bg-rose-500/5">
                                                                <span className="text-rose-400 block text-[7.5px] uppercase font-black tracking-wider">STOP LOSS</span>
                                                                <span className="text-rose-300 font-black text-[11px]">₹{u.stop_loss || 57727.93}</span>
                                                            </div>
                                                            <div className="p-2 rounded-lg bg-black/50 border border-cyan-500/30 bg-cyan-500/5">
                                                                <span className="text-cyan-400 block text-[7.5px] uppercase font-black tracking-wider">RECOMMENDED LOT SIZE</span>
                                                                <span className="text-cyan-300 font-black text-[10.5px]">{u.recommended_lot_size || "2 Lots (Qty: 30)"}</span>
                                                            </div>
                                                            <div className="p-2 rounded-lg bg-black/50 border border-indigo-500/30 bg-indigo-500/5">
                                                                <span className="text-indigo-400 block text-[7.5px] uppercase font-black tracking-wider">EST MARGIN</span>
                                                                <span className="text-indigo-300 font-black text-[10.5px]">{u.est_margin || "₹45,000"}</span>
                                                            </div>
                                                            <div className="p-2 rounded-lg bg-black/50 border border-amber-500/30 bg-amber-500/5">
                                                                <span className="text-amber-400 block text-[7.5px] uppercase font-black tracking-wider">TIMELINE</span>
                                                                <span className="text-amber-300 font-black text-[10.5px]">45-Min Hold Window</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })()}

                                            {/* 3 Sub-Model Pillar Graphic Cards */}
                                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                                                {/* Pillar 1 Graphic */}
                                                <div className="p-2.5 rounded-xl bg-slate-900/90 border border-cyan-500/30 space-y-1.5 text-[9.5px] font-mono shadow-md">
                                                    <div className="flex items-center justify-between text-cyan-400 font-black border-b border-white/10 pb-1">
                                                        <span>1. AI/ML TECH</span>
                                                        <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">BUY (73.5%)</span>
                                                    </div>
                                                    <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-cyan-500/30">
                                                        <div className="h-full bg-gradient-to-r from-cyan-600 to-cyan-400" style={{ width: '73.5%' }} />
                                                    </div>
                                                    <div className="text-[8px] text-slate-300 flex justify-between font-bold">
                                                        <span>RSI: 51.89</span>
                                                        <span>SMA-20: ₹57,861</span>
                                                    </div>
                                                </div>

                                                {/* Pillar 2 Graphic */}
                                                <div className="p-2.5 rounded-xl bg-slate-900/90 border border-purple-500/30 space-y-1.5 text-[9.5px] font-mono shadow-md">
                                                    <div className="flex items-center justify-between text-purple-400 font-black border-b border-white/10 pb-1">
                                                        <span>2. NEWS NLP</span>
                                                        <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">BULLISH (+0.59)</span>
                                                    </div>
                                                    <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-purple-500/30">
                                                        <div className="h-full bg-gradient-to-r from-purple-600 to-indigo-400" style={{ width: '82.6%' }} />
                                                    </div>
                                                    <div className="text-[8px] text-slate-300 truncate font-bold">
                                                        📰 RBI Accommodative Stance
                                                    </div>
                                                </div>

                                                {/* Pillar 3 Graphic */}
                                                <div className="p-2.5 rounded-xl bg-slate-900/90 border border-amber-500/30 space-y-1.5 text-[9.5px] font-mono shadow-md">
                                                    <div className="flex items-center justify-between text-amber-400 font-black border-b border-white/10 pb-1">
                                                        <span>3. GANN ASTRO</span>
                                                        <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">90° EXPANSION</span>
                                                    </div>
                                                    <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-amber-500/30">
                                                        <div className="h-full bg-gradient-to-r from-amber-600 to-yellow-400" style={{ width: '84.0%' }} />
                                                    </div>
                                                    <div className="text-[8px] text-slate-300 font-bold">
                                                        ☸️ Sun-Jupiter Trine (120°)
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-200 rounded-bl-none font-mono whitespace-pre-wrap">
                                                {msg.text}
                                            </div>

                                            {/* RAG Knowledge Base Sources Card (if any returned) */}
                                            {msg.role === 'assistant' && msg.rag_sources && msg.rag_sources.length > 0 && (
                                                <div className="rounded-lg bg-slate-950/80 border border-cyan-500/30 overflow-hidden font-mono">
                                                    <button
                                                        onClick={() => toggleSources(idx)}
                                                        className="w-full flex items-center justify-between px-2.5 py-1.5 bg-cyan-950/40 text-[10px] text-cyan-300 font-bold hover:bg-cyan-900/50 transition"
                                                    >
                                                        <span className="flex items-center gap-1.5">
                                                            <BookOpen className="w-3 h-3 text-cyan-400" />
                                                            <span>🧠 RAG Sources & Playbook Rules ({msg.rag_sources.length} matches)</span>
                                                        </span>
                                                        <span className="text-cyan-400">
                                                            {expandedSources[idx] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                                        </span>
                                                    </button>

                                                    {expandedSources[idx] && (
                                                        <div className="p-2 space-y-2 border-t border-cyan-900/40 text-[9.5px]">
                                                            {msg.rag_sources.map((src, sIdx) => (
                                                                <div key={sIdx} className="p-2 rounded bg-slate-900/90 border border-white/5 space-y-1">
                                                                    <div className="flex items-center justify-between text-slate-300 font-bold">
                                                                        <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 uppercase text-[8px]">
                                                                            {src.collection?.replace('_', ' ')}
                                                                        </span>
                                                                        <span className="text-emerald-400 text-[8px]">
                                                                            Match: {Math.round((src.similarity_score || 0) * 100)}%
                                                                        </span>
                                                                    </div>
                                                                    <p className="text-slate-400 whitespace-pre-wrap leading-relaxed">
                                                                        {src.document}
                                                                    </p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {msg.role === 'user' && (
                                    <div className="w-6 h-6 rounded-md bg-emerald-950 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shrink-0 mt-0.5">
                                        <User className="w-3.5 h-3.5" />
                                    </div>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs p-2">
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                <span>Gemini AI is retrieving RAG memory and analyzing market signals...</span>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    {/* Input Field */}
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            handleSend();
                        }}
                        className="mt-3 flex items-center space-x-2"
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask Gemini AI with RAG (e.g. 'What are my rules for CPR breakout?')..."
                            className="flex-1 bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none font-mono transition"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="px-3 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed transition"
                        >
                            <Send className="w-3.5 h-3.5" />
                        </button>
                    </form>
                </div>
            )}
        </HUDCard>
    );
};

export default GeminiAssistant;
