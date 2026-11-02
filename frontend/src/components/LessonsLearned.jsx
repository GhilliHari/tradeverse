import React, { useState, useEffect } from 'react';
import { BookOpen, CheckCircle2, ShieldCheck, Database, Cpu, Sparkles, Search, PlusCircle, Layers, RefreshCw, AlertCircle } from 'lucide-react';
import HUDCard from './ui/HUDCard';
import { API_URL } from '../config/api';

const LessonsLearned = () => {
    const [ragStats, setRagStats] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCollection, setSelectedCollection] = useState('all');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);

    // New Document Form State
    const [newDocContent, setNewDocContent] = useState('');
    const [newDocCollection, setNewDocCollection] = useState('trader_journal');
    const [addLoading, setAddLoading] = useState(false);
    const [addSuccess, setAddSuccess] = useState(null);

    const getUrl = (path) => `${(API_URL || '').replace(/\/$/, '')}${path}`;

    // Fetch initial RAG Stats
    const fetchRagStats = async () => {
        try {
            const res = await fetch(getUrl('/api/rag/stats'));
            const data = await res.json();
            setRagStats(data);
        } catch (err) {
            console.error("Failed to fetch RAG stats:", err);
        }
    };

    useEffect(() => {
        fetchRagStats();
    }, []);

    // Handle Search
    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        if (!searchQuery.trim()) return;

        setSearchLoading(true);
        try {
            const colParam = selectedCollection !== 'all' ? `&collection=${selectedCollection}` : '';
            const res = await fetch(getUrl(`/api/rag/search?query=${encodeURIComponent(searchQuery)}${colParam}&top_k=4`));
            const data = await res.json();
            setSearchResults(data?.results || []);
        } catch (err) {
            console.error("RAG search failed:", err);
        } finally {
            setSearchLoading(false);
        }
    };

    // Handle Add Document
    const handleAddDocument = async (e) => {
        e.preventDefault();
        if (!newDocContent.trim()) return;

        setAddLoading(true);
        setAddSuccess(null);
        try {
            const res = await fetch(getUrl('/api/rag/documents'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: newDocContent,
                    collection_name: newDocCollection,
                    metadata: { source: 'user_ui', timestamp: new Date().toISOString() }
                })
            });
            const data = await res.json();
            if (data?.status === 'success') {
                setAddSuccess(`✅ Successfully indexed rule into '${newDocCollection}'!`);
                setNewDocContent('');
                fetchRagStats();
            } else {
                setAddSuccess(`❌ Error: ${data?.message || 'Failed to add rule'}`);
            }
        } catch (err) {
            console.error("Failed to add document:", err);
            setAddSuccess(`❌ Connection error to RAG server`);
        } finally {
            setAddLoading(false);
        }
    };

    const lessons = [
        {
            category: "1. EMBEDDED RAG & VECTOR MEMORY",
            icon: BookOpen,
            color: "text-cyan-400",
            borderColor: "border-cyan-500/20",
            bgColor: "bg-cyan-500/5",
            items: [
                { title: "Zero-Cost Embedded ChromaDB", detail: "Vector store runs in-process with persistent SQLite/Parquet files in 'backend/knowledge_base/chroma_db'. No external database clusters or cloud charges required." },
                { title: "Quant Playbook & Regime Grounding", detail: "RAG injects verified CPR breakout rules, Gamma wall strategies, and historical event case studies directly into Gemini prompts to eliminate hallucinations." }
            ]
        },
        {
            category: "2. COST & INFRASTRUCTURE GUARANTEE",
            icon: ShieldCheck,
            color: "text-emerald-400",
            borderColor: "border-emerald-500/20",
            bgColor: "bg-emerald-500/5",
            items: [
                { title: "Strict Zero-Cost Preference", detail: "All model training, multi-year backtests, and AI features use free tier resources (BigQuery Free Sandbox, Google AI Studio Free API)." },
                { title: "Disk Space Optimization", detail: "Multi-year data is stored in BigQuery Sandbox rather than eating local Mac disk space." }
            ]
        },
        {
            category: "3. QUANTITATIVE ACCURACY & PRECISION",
            icon: Cpu,
            color: "text-purple-400",
            borderColor: "border-purple-500/20",
            bgColor: "bg-purple-500/5",
            items: [
                { title: "3-Digit Float Precision", detail: "All PCR sentiment (e.g. 1.065) and AI Confidence metrics (e.g. 36.886%) are strictly rounded to 3 decimal places across backend APIs and UI components." },
                { title: "24/7 Resilience & GEX Fallback", detail: "When live broker feeds disconnect after market hours, Tradeverse automatically falls back to Simulation Mode so GEX scanner & option chains stay online 24/7." }
            ]
        },
        {
            category: "4. BIGQUERY 12-YEAR VALIDATION PIPELINE",
            icon: Database,
            color: "text-amber-400",
            borderColor: "border-amber-500/20",
            bgColor: "bg-amber-500/5",
            items: [
                { title: "10Y Train / 2Y Test Split", detail: "Dataset 'tradeverse-fe8ef.tradeverse_analytics' evaluates 10Y In-Sample (2014-2024) vs 2Y Out-of-Sample (2024-2026) to eliminate lookahead bias." },
                { title: "Dataplex & Auto-Cleaning Protocol", detail: "Market candle gaps are forward-filled (ffill), price spikes (>5-Sigma) are neutralized, and high/low consistency is strictly enforced." }
            ]
        }
    ];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 font-mono">
            {/* Main Knowledge Base Header */}
            <HUDCard title="RAG KNOWLEDGE BASE & QUANT PLAYBOOK VECTOR ENGINE" neonColor="cyan">
                <div className="p-6 space-y-6">
                    {/* Status Banner */}
                    <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-cyan-300 bg-cyan-950/40 p-4 rounded-2xl border border-cyan-800/40">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 rounded-xl bg-cyan-500/20 border border-cyan-500/40">
                                <BookOpen className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div>
                                <div className="font-bold text-sm text-white flex items-center gap-2">
                                    <span>CHROMADB VECTOR MEMORY</span>
                                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                                </div>
                                <div className="text-[10px] text-slate-400 mt-0.5">
                                    Embedded Semantic Knowledge Base for Playbooks, Historical Regimes & Personal Rules
                                </div>
                            </div>
                        </div>

                        {/* Collection Count Pills */}
                        <div className="flex flex-wrap gap-2 text-[10px]">
                            {ragStats?.collections && Object.entries(ragStats.collections).map(([col, count]) => (
                                <div key={col} className="px-2.5 py-1 rounded-lg bg-slate-900/90 border border-cyan-500/30 flex items-center gap-1.5">
                                    <span className="text-slate-400 capitalize">{col.replace('_', ' ')}:</span>
                                    <span className="text-cyan-300 font-bold">{count} docs</span>
                                </div>
                            ))}
                            <button
                                onClick={fetchRagStats}
                                className="p-1 text-slate-400 hover:text-cyan-300 transition"
                                title="Refresh RAG Stats"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    </div>

                    {/* Interactive RAG Search and Ingestion Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* Search Explorer (7 cols) */}
                        <div className="lg:col-span-7 p-4 rounded-2xl bg-slate-900/90 border border-cyan-500/20 space-y-4">
                            <div className="flex items-center justify-between border-b border-white/5 pb-2">
                                <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs">
                                    <Search className="w-4 h-4" />
                                    <span>SEMANTIC VECTOR SEARCH</span>
                                </div>
                                <span className="text-[10px] text-slate-500">Cosine Distance Metric</span>
                            </div>

                            {/* Search Bar */}
                            <form onSubmit={handleSearch} className="space-y-2">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        placeholder="Search playbooks (e.g. 'CPR breakout' or 'Budget day IV crush')..."
                                        className="flex-1 bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 outline-none transition"
                                    />
                                    <button
                                        type="submit"
                                        disabled={searchLoading || !searchQuery.trim()}
                                        className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 disabled:opacity-50 transition"
                                    >
                                        {searchLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                                        <span>Search</span>
                                    </button>
                                </div>

                                <div className="flex items-center gap-2 text-[10px]">
                                    <span className="text-slate-400">Target Collection:</span>
                                    {['all', 'trading_playbook', 'historical_regimes', 'banking_research', 'trader_journal'].map((col) => (
                                        <button
                                            key={col}
                                            type="button"
                                            onClick={() => setSelectedCollection(col)}
                                            className={`px-2 py-0.5 rounded capitalize transition ${
                                                selectedCollection === col
                                                    ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 font-bold'
                                                    : 'text-slate-500 hover:text-slate-300'
                                            }`}
                                        >
                                            {col.replace('_', ' ')}
                                        </button>
                                    ))}
                                </div>
                            </form>

                            {/* Search Results */}
                            <div className="space-y-2.5 max-h-[260px] overflow-y-auto pr-1">
                                {searchResults.length > 0 ? (
                                    searchResults.map((res, rIdx) => (
                                        <div key={rIdx} className="p-3 rounded-xl bg-slate-950/70 border border-cyan-500/20 space-y-1.5">
                                            <div className="flex items-center justify-between text-[10px]">
                                                <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 uppercase font-bold text-[9px]">
                                                    {res.collection?.replace('_', ' ')}
                                                </span>
                                                <span className="text-emerald-400 font-bold">
                                                    Match: {Math.round((res.similarity_score || 0) * 100)}%
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-slate-300 whitespace-pre-wrap leading-relaxed">
                                                {res.document}
                                            </p>
                                        </div>
                                    ))
                                ) : (
                                    <div className="p-6 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
                                        Type a trading question or query above to test semantic retrieval across your indexed knowledge base.
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Add Rule / Document Form (5 cols) */}
                        <div className="lg:col-span-5 p-4 rounded-2xl bg-slate-900/90 border border-purple-500/20 space-y-4">
                            <div className="flex items-center justify-between border-b border-white/5 pb-2">
                                <div className="flex items-center space-x-2 text-purple-400 font-bold text-xs">
                                    <PlusCircle className="w-4 h-4" />
                                    <span>ADD RULE / PLAYBOOK ENTRY</span>
                                </div>
                                <span className="text-[10px] text-slate-500">Live Ingestion</span>
                            </div>

                            <form onSubmit={handleAddDocument} className="space-y-3">
                                <div>
                                    <label className="text-[10px] text-slate-400 block mb-1">Target Knowledge Collection</label>
                                    <select
                                        value={newDocCollection}
                                        onChange={(e) => setNewDocCollection(e.target.value)}
                                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-purple-500 font-mono"
                                    >
                                        <option value="trader_journal">Trader Journal & Personal Rules</option>
                                        <option value="trading_playbook">Trading Playbook (GEX, CPR, VWAP)</option>
                                        <option value="historical_regimes">Historical Market Regimes</option>
                                        <option value="banking_research">Banking Sector Research</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="text-[10px] text-slate-400 block mb-1">Rule / Playbook Content</label>
                                    <textarea
                                        rows={4}
                                        value={newDocContent}
                                        onChange={(e) => setNewDocContent(e.target.value)}
                                        placeholder="e.g. 'Rule: If Bank Nifty opens with >1% gap up into Upper Call Wall, wait for first 15-min candle pullback before entering...'"
                                        className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-purple-500 font-mono leading-relaxed"
                                    />
                                </div>

                                {addSuccess && (
                                    <div className="text-[10px] text-slate-300 bg-slate-950 p-2 rounded-lg border border-purple-500/30">
                                        {addSuccess}
                                    </div>
                                )}

                                <button
                                    type="submit"
                                    disabled={addLoading || !newDocContent.trim()}
                                    className="w-full py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 transition"
                                >
                                    {addLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <PlusCircle className="w-3.5 h-3.5" />}
                                    <span>Index Into ChromaDB Vector Memory</span>
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Architectural Principles & Lessons Learned Grid */}
                    <div className="pt-2">
                        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
                            PERSISTED ARCHITECTURAL PATTERNS
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {lessons.map((section, idx) => {
                                const IconComponent = section.icon;
                                return (
                                    <div key={idx} className={`p-5 rounded-2xl bg-slate-900/80 border ${section.borderColor} space-y-4`}>
                                        <div className="flex items-center space-x-2 border-b border-white/5 pb-2">
                                            <IconComponent className={`w-4 h-4 ${section.color}`} />
                                            <h3 className={`text-xs font-black uppercase tracking-wider ${section.color}`}>{section.category}</h3>
                                        </div>
                                        <div className="space-y-3">
                                            {section.items.map((item, itemIdx) => (
                                                <div key={itemIdx} className="space-y-1">
                                                    <div className="text-xs font-bold text-white flex items-center gap-1.5">
                                                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                                        {item.title}
                                                    </div>
                                                    <p className="text-[10px] text-slate-400 leading-relaxed pl-4">
                                                        {item.detail}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </HUDCard>
        </div>
    );
};

export default LessonsLearned;
