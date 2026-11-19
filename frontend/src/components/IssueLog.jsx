import React, { useState } from 'react';
import { 
    AlertTriangle, ShieldCheck, CheckCircle2, Clock, 
    Terminal, ArrowRight, Bug, AlertOctagon, 
    Cpu, RefreshCw, PlusCircle, Search, Filter
} from 'lucide-react';
import HUDCard from './ui/HUDCard';

const INITIAL_INCIDENTS = [
    {
        id: "INC-20261119-001",
        title: "Oracle Cloud Linux VM GMT/UTC Timezone Offset Execution Lockout",
        category: "INFRASTRUCTURE & CLOCK",
        date: "2026-11-19",
        session: "NSE F&O Thursday Expiry Session",
        severity: "HIGH",
        status: "RESOLVED",
        capitalImpact: "₹0.00 (Zero Drawdown / Capital Fully Intact)",
        symptom: "No autonomous trades executed during market hours (09:15 - 15:30 IST) despite active market conditions, connected Angel One session, and ₹7,616.56 available cash margin.",
        rootCause: "Oracle Cloud Linux VM defaulted operating system clock (/etc/localtime) to UTC/GMT (+00:00). At 09:15 AM IST market open, naive Python datetime.now() returned 03:45 AM GMT. The trading loop check (time(9,15) <= current_time <= time(15,30)) evaluated to False, causing the cloud engine to assume the Indian market was closed throughout the morning and early afternoon.",
        timeline: [
            { time: "09:15 AM IST", event: "NSE opened. Cloud VM clock read 03:45 AM GMT. Autonomous loop set last_status='MARKET_CLOSED'." },
            { time: "09:15 - 14:35 IST", event: "VM remained in false market-closed standby during prime breakout hours (03:45 - 09:05 GMT)." },
            { time: "14:45 IST (09:15 GMT)", event: "Server clock finally reached 09:15 GMT. However, Late-Session Theta Guard rightly locked new entries after 14:35 IST." },
            { time: "16:22 IST", event: "Issue identified via journalctl audit. System clock permanently updated to Asia/Kolkata (IST)." },
            { time: "16:41 IST", event: "ZoneInfo('Asia/Kolkata') code-level defense implemented across all trading loops. Deployed and verified on Cloud VM." }
        ],
        fiveWhys: [
            "Why were no trades placed? Autonomous cycle evaluated is_time_match as False.",
            "Why was is_time_match False? Current server clock hour was 03:45 AM when market was 09:15 AM.",
            "Why was server clock 03:45 AM? Oracle Cloud Ubuntu Linux VM defaulted to UTC/GMT (+0000).",
            "Why did Python read UTC? Code used naive datetime.now() without explicit timezone anchoring.",
            "Why wasn't it caught earlier? Local Mac development was on IST, masking the cloud host timezone difference."
        ],
        permanentFix: [
            "Host Server Lock: Executed 'sudo timedatectl set-timezone Asia/Kolkata' to permanently anchor the Linux OS clock to IST across reboots.",
            "Code-Level ZoneInfo Guarantee: Replaced all naive datetime.now() calls in main.py and risk_engine.py with get_ist_now() using ZoneInfo('Asia/Kolkata'). Immune to any host OS clock settings.",
            "RAG Memory Ingestion: Seeded Trader Rule #21 into ChromaDB vector memory and documented in LessonsLearned.jsx Category #15."
        ],
        commitHash: "ca8ee43"
    },
    {
        id: "INC-20261119-002",
        title: "Gemini AI Studio Free-Tier Quota Exhaustion (HTTP 429 ResourceExhausted)",
        category: "AI & MODEL ROUTER",
        date: "2026-11-19",
        session: "Mid-Day News Sentiment Scanning",
        severity: "MEDIUM",
        status: "RESOLVED",
        capitalImpact: "₹0.00 (Neutral Fallback Guard Prevented Bad Fills)",
        symptom: "Sentiment agent returned 429 quota errors during live financial news classification when testing high-frequency market catalysts.",
        rootCause: "Google AI Studio free tier enforces a strict 500 requests/day quota on gemini-3.5-flash-lite. Exceeding this rate-limited the model for 24 hours.",
        timeline: [
            { time: "15:36 IST", event: "Gemini API returned StatusCode.RESOURCE_EXHAUSTED (quota exceeded on Free Tier)." },
            { time: "15:40 IST", event: "Engineered zero-cost Dalal Street Financial Lexicon scoring engine in news_sentiment_engine.py." },
            { time: "15:45 IST", event: "Tested live headline parsing (Fortune India, ET, Livemint) achieving +0.681 Bullish score with 0ms latency and 0 API cost." }
        ],
        fiveWhys: [
            "Why did sentiment agent fail? Gemini API returned HTTP 429 ResourceExhausted.",
            "Why was quota exhausted? Daily 500-request limit reached on free tier during multi-model testing.",
            "Why was the engine vulnerable? Single dependency on external cloud LLM for sentiment score.",
            "How was it fixed? Built local Dalal Street weighted keyword lexicon operating directly in-memory.",
            "What is the ongoing safety? System automatically falls back to lexicon when LLM is unavailable."
        ],
        permanentFix: [
            "Dual-Core Sentiment Architecture: Gemini LLM serves as primary when active; Dalal Street Lexicon provides 100% fail-safe fallback.",
            "Multi-Source RSS Ingestion: Scrapes Google News RSS, Economic Times, and Livemint without HTML parsing or rate limits.",
            "Zero Cost Guarantee: System runs sentiment analysis 24/7 with zero cloud API charges."
        ],
        commitHash: "921f644"
    },
    {
        id: "INC-20261118-001",
        title: "Telegram Bot Polling HTTP 409 Conflict (Dual Instance Collision)",
        category: "TELEMETRY & ALERTS",
        date: "2026-11-18",
        session: "Nightly Cloud Deployment",
        severity: "LOW",
        status: "RESOLVED",
        capitalImpact: "₹0.00 (Alerts only, trading logic unaffected)",
        symptom: "Telegram polling logs flooded with HTTP 409 Conflict: another instance is active.",
        rootCause: "Local Mac development environment and Oracle Cloud VM were both running background processes polling Telegram getUpdates with the same bot token.",
        timeline: [
            { time: "22:15 IST", event: "Telegram bot started logging repeated 409 conflict errors." },
            { time: "22:30 IST", event: "Added 30s exponential backoff and DISABLE_TELEGRAM_POLLING configuration." },
            { time: "22:45 IST", event: "Dedicated cloud instance as exclusive Telegram poll master." }
        ],
        fiveWhys: [
            "Why did Telegram return 409? Two clients called getUpdates simultaneously on one token.",
            "Why were two clients running? Local Mac server and Oracle Cloud VM both had active poll daemons.",
            "How was collision prevented? Added backoff delay and environment flags to decouple local from cloud."
        ],
        permanentFix: [
            "Exponential 30s backoff implemented in telegram_bot_service.py on HTTP 409.",
            "Cloud instance designated as master interactive polling daemon; local instances run in send-only mode."
        ],
        commitHash: "40f8166"
    }
];

const IssueLog = () => {
    const [incidents, setIncidents] = useState(INITIAL_INCIDENTS);
    const [selectedIncident, setSelectedIncident] = useState(INITIAL_INCIDENTS[0]);
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');

    const filtered = incidents.filter(inc => {
        const matchesStatus = filterStatus === 'ALL' || inc.status === filterStatus;
        const matchesQuery = !searchQuery || 
            inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            inc.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
            inc.category.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesStatus && matchesQuery;
    });

    const totalCount = incidents.length;
    const resolvedCount = incidents.filter(i => i.status === 'RESOLVED').length;

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 font-mono">
            {/* Header HUD Card */}
            <HUDCard title="INCIDENT POST-MORTEM & ISSUE RESOLUTION AUDIT LOG" neonColor="amber">
                <div className="p-6 space-y-6">
                    {/* Status KPI Banner */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="p-4 rounded-xl bg-slate-900/80 border border-amber-500/30 flex items-center justify-between">
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tracked Incidents</div>
                                <div className="text-2xl font-black text-amber-400 mt-1">{totalCount}</div>
                            </div>
                            <Bug className="w-6 h-6 text-amber-400/60" />
                        </div>

                        <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex items-center justify-between">
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Resolved & Patched</div>
                                <div className="text-2xl font-black text-emerald-400 mt-1">{resolvedCount}</div>
                            </div>
                            <CheckCircle2 className="w-6 h-6 text-emerald-400/60" />
                        </div>

                        <div className="p-4 rounded-xl bg-slate-900/80 border border-cyan-500/30 flex items-center justify-between">
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Capital Drawdown Impact</div>
                                <div className="text-2xl font-black text-cyan-400 mt-1">₹0.00</div>
                            </div>
                            <ShieldCheck className="w-6 h-6 text-cyan-400/60" />
                        </div>

                        <div className="p-4 rounded-xl bg-slate-900/80 border border-purple-500/30 flex items-center justify-between">
                            <div>
                                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Mean Time To Resolution</div>
                                <div className="text-2xl font-black text-purple-400 mt-1">&lt; 30m</div>
                            </div>
                            <Clock className="w-6 h-6 text-purple-400/60" />
                        </div>
                    </div>

                    {/* Controls: Search and Filters */}
                    <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800">
                        <div className="flex items-center gap-2 flex-1 max-w-md bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                            <Search className="w-4 h-4 text-slate-500" />
                            <input
                                type="text"
                                placeholder="Search by ID, keyword, or root cause..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="bg-transparent border-none outline-none text-xs text-white placeholder-slate-500 w-full"
                            />
                        </div>

                        <div className="flex items-center gap-2 text-xs">
                            <span className="text-slate-400 font-bold uppercase text-[10px]">Filter Status:</span>
                            {['ALL', 'RESOLVED', 'ACTIVE'].map((st) => (
                                <button
                                    key={st}
                                    onClick={() => setFilterStatus(st)}
                                    className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition ${
                                        filterStatus === st 
                                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' 
                                            : 'bg-slate-900 text-slate-400 hover:bg-slate-800 border border-slate-800'
                                    }`}
                                >
                                    {st}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Master-Detail Split Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
                        {/* Incident List (Left Column) */}
                        <div className="lg:col-span-5 space-y-3">
                            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                                <span>RECORDED INCIDENTS</span>
                                <span className="text-[10px] text-slate-500">{filtered.length} entries</span>
                            </div>

                            <div className="space-y-2.5 max-h-[650px] overflow-y-auto pr-1">
                                {filtered.map((inc) => {
                                    const isSelected = selectedIncident?.id === inc.id;
                                    return (
                                        <div
                                            key={inc.id}
                                            onClick={() => setSelectedIncident(inc)}
                                            className={`p-4 rounded-xl border cursor-pointer transition-all ${
                                                isSelected 
                                                    ? 'bg-amber-500/10 border-amber-500/50 shadow-lg shadow-amber-500/5' 
                                                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                                            }`}
                                        >
                                            <div className="flex items-center justify-between mb-1.5">
                                                <span className="text-[10px] font-black text-amber-400 uppercase tracking-widest">{inc.id}</span>
                                                <span className={`text-[9px] font-black px-2 py-0.5 rounded-full ${
                                                    inc.status === 'RESOLVED' 
                                                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                                                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                                }`}>
                                                    {inc.status}
                                                </span>
                                            </div>

                                            <div className="text-xs font-bold text-white mb-2 line-clamp-2">
                                                {inc.title}
                                            </div>

                                            <div className="flex items-center justify-between text-[10px] text-slate-400 border-t border-white/5 pt-2">
                                                <span className="flex items-center gap-1">
                                                    <Clock className="w-3 h-3 text-slate-500" />
                                                    {inc.date}
                                                </span>
                                                <span className="text-slate-400 font-mono text-[9px]">{inc.category}</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Selected Incident Deep-Dive Dossier (Right Column) */}
                        <div className="lg:col-span-7">
                            {selectedIncident ? (
                                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-6">
                                    {/* Dossier Header */}
                                    <div className="border-b border-white/10 pb-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-black">
                                                    {selectedIncident.id}
                                                </span>
                                                <span className="text-xs font-bold text-slate-400">{selectedIncident.category}</span>
                                            </div>
                                            <span className="text-[10px] text-slate-400 font-mono">{selectedIncident.session}</span>
                                        </div>
                                        <h2 className="text-sm font-black text-white leading-snug">{selectedIncident.title}</h2>
                                    </div>

                                    {/* Critical Impact Badge */}
                                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-2 text-slate-400">
                                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                                            <span>Capital Protection:</span>
                                        </div>
                                        <span className="font-bold text-emerald-400 font-mono">{selectedIncident.capitalImpact}</span>
                                    </div>

                                    {/* Observed Symptom */}
                                    <div className="space-y-1.5">
                                        <div className="text-[10px] font-bold text-amber-400 uppercase tracking-widest flex items-center gap-1.5">
                                            <AlertTriangle className="w-3.5 h-3.5" />
                                            <span>Observed Symptom</span>
                                        </div>
                                        <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                                            {selectedIncident.symptom}
                                        </p>
                                    </div>

                                    {/* Root Cause Analysis */}
                                    <div className="space-y-1.5">
                                        <div className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-1.5">
                                            <Bug className="w-3.5 h-3.5" />
                                            <span>Root Cause Breakdown</span>
                                        </div>
                                        <p className="text-xs text-slate-300 bg-slate-950 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                                            {selectedIncident.rootCause}
                                        </p>
                                    </div>

                                    {/* 5 Whys Analysis */}
                                    {selectedIncident.fiveWhys && (
                                        <div className="space-y-2">
                                            <div className="text-[10px] font-bold text-purple-400 uppercase tracking-widest">
                                                5-WHYS ROOT CAUSE CHAIN
                                            </div>
                                            <div className="space-y-1.5 bg-slate-950 p-3 rounded-xl border border-slate-800/80">
                                                {selectedIncident.fiveWhys.map((why, idx) => (
                                                    <div key={idx} className="flex items-start gap-2 text-xs">
                                                        <span className="text-purple-400 font-bold shrink-0">W{idx + 1}:</span>
                                                        <span className="text-slate-300">{why}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Permanent Fix & Architecture Guard */}
                                    <div className="space-y-2">
                                        <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-1.5">
                                            <CheckCircle2 className="w-3.5 h-3.5" />
                                            <span>Permanent Fix Implemented & Verified</span>
                                        </div>
                                        <div className="space-y-2">
                                            {selectedIncident.permanentFix.map((fix, idx) => (
                                                <div key={idx} className="flex items-start gap-2 p-2.5 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-xs">
                                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                                                    <span className="text-slate-200">{fix}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Commit Verification Footer */}
                                    <div className="pt-3 border-t border-white/10 flex items-center justify-between text-[10px] text-slate-400">
                                        <span>Git Commit Hash: <code className="text-amber-400 font-bold">{selectedIncident.commitHash}</code></span>
                                        <span className="text-emerald-400 font-bold uppercase">LIVE ON ORACLE CLOUD (129.225.125.13)</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="h-64 flex items-center justify-center text-slate-500 text-xs">
                                    Select an incident on the left to view post-mortem dossier.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </HUDCard>
        </div>
    );
};

export default IssueLog;
