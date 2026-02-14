import React from 'react';
import { BookOpen, AlertTriangle, CheckCircle2, ShieldAlert, Database, Key } from 'lucide-react';

const LessonCard = ({ title, type, date, mistake, solution, icon: Icon, color }) => (
    <div className="bg-black/40 border border-white/5 rounded-3xl p-8 hover:border-white/10 transition-all group overflow-hidden relative">
        <div className={`absolute top-0 right-0 w-32 h-32 bg-${color}-500/5 blur-[50px] rounded-full -mr-16 -mt-16 group-hover:bg-${color}-500/10 transition-all`} />

        <div className="flex items-start gap-4 mb-6 relative">
            <div className={`p-3 rounded-2xl bg-${color}-500/10 border border-${color}-500/20`}>
                <Icon className={`w-6 h-6 text-${color}-400`} />
            </div>
            <div>
                <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-black text-white tracking-tight">{title}</h3>
                    <span className={`px-2 py-0.5 rounded-full bg-${color}-500/10 border border-${color}-500/20 text-[8px] font-black uppercase tracking-widest text-${color}-400`}>
                        {type}
                    </span>
                </div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{date}</p>
            </div>
        </div>

        <div className="space-y-6 relative">
            <div className="space-y-2">
                <div className="flex items-center gap-2 text-red-400">
                    <AlertTriangle className="w-3 h-3" />
                    <span className="text-[10px] font-black uppercase tracking-widest">The Mistake</span>
                </div>
                <p className="text-sm text-slate-400 leading-relaxed pl-5 border-l border-red-500/20">
                    {mistake}
                </p>
            </div>

            <div className="space-y-2">
                <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" />
                    <span className="text-[10px] font-black uppercase tracking-widest">The Lesson / Fix</span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed pl-5 border-l border-emerald-500/20">
                    {solution}
                </p>
            </div>
        </div>
    </div>
);

const LessonsLearned = () => {
    const lessons = [
        {
            title: "Strict Credential Validation",
            type: "Security",
            date: "Feb 13, 2026",
            mistake: "The system was accepting invalid API credentials and showing a 'Connected' status because it silently fell back to a Mock profile when the real login failed.",
            solution: "Implemented strict session verification. The backend now hard-blocks Live mode switches until Angel One confirms a valid JWT session, and provides real-time error feedback (e.g., 'Invalid TOTP').",
            icon: ShieldAlert,
            color: "rose"
        },
        {
            title: "Persistent State Architecture",
            type: "Infrastructure",
            date: "Feb 13, 2026",
            mistake: "Credentials and environment settings were only stored in an in-memory Redis mock, causing complete data loss whenever the backend server restarted.",
            solution: "Created a dual-layer persistence system. Settings are now written to 'settings.json' on disk immediately upon update, ensuring full recovery across reboots.",
            icon: Database,
            color: "indigo"
        },
        {
            title: "Index LTP Mapping Logic",
            type: "Data Engine",
            date: "Feb 12, 2026",
            mistake: "Automated trading was failing because index tokens (BANKNIFTY/NIFTY) weren't being correctly mapped to their specific Angel One instrument IDs in the background agent.",
            solution: "Refactored the Token Manager to include institutional-grade heuristic mapping for major indices, ensuring the 'Intelligence Layer' always receives real-time liquidity data.",
            icon: Key,
            color: "amber"
        }
    ];

    return (
        <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex flex-col gap-2">
                <h2 className="text-4xl font-black text-white tracking-tighter flex items-center gap-4">
                    <BookOpen className="w-10 h-10 text-indigo-500" />
                    LESSONS LEARNED
                </h2>
                <p className="text-slate-500 font-bold uppercase tracking-[0.3em] text-[10px] ml-1">
                    Engineering Journal of System Evolutions & Mistake Rectification
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {lessons.map((lesson, idx) => (
                    <LessonCard key={idx} {...lesson} />
                ))}
            </div>

            <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-3xl p-8 flex items-center justify-between">
                <div className="space-y-1">
                    <h4 className="text-indigo-400 font-black text-sm uppercase tracking-widest">Ongoing Mission</h4>
                    <p className="text-slate-400 text-sm">Every failure is a data point for a more resilient Tradeverse.</p>
                </div>
                <div className="text-[8px] font-black text-slate-600 uppercase tracking-widest text-right">
                    BUILD ID: stable-v9.3-cortex<br />
                    KERNEL: AI-REINFORCED-v2
                </div>
            </div>
        </div>
    );
};

export default LessonsLearned;
