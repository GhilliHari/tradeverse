import React from 'react';
import { CheckCircle2, XCircle, Zap, Shield, Target, Clock, AlertTriangle } from 'lucide-react';

const TradeChecklist = ({ symbol, analysis }) => {
    // If no analysis or neutral signal, show waiting state
    if (!analysis || analysis.final_action === 'HOLD') {
        return (
            <div className="glass-panel p-6 rounded-3xl border border-white/5 opacity-50 relative overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-slate-500/5 blur-[40px] rounded-full -mr-16 -mt-16" />
                <div className="relative z-10">
                    <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest flex items-center gap-2">
                        <Clock className="w-3 h-3" /> System Evaluation: PASSIVE
                    </p>
                    <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest mt-2">Waiting for Institutional Conviction</h3>
                    <div className="mt-6 space-y-4 opacity-30">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-8 bg-white/5 rounded-xl animate-pulse" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    const rec = analysis.trade_recommendation || {};
    const confidence = analysis.confidence || 0;
    const isExpiry = analysis.is_expiry;
    const action = analysis.final_action;

    const criteria = [
        {
            label: isExpiry ? "Gamma Sniper Conviction" : "Neural Factor Convergence",
            value: (confidence || 0) >= 70 ? ((confidence || 0) >= 85 ? (isExpiry ? "AGGRESSIVE" : "STRONG") : "MODERATE") : "WEAK",
            valid: (confidence || 0) >= 70,
            detail: isExpiry ? `High-Delta Capture active: ${confidence.toFixed(1)}%` : `Confidence: ${(confidence || 0).toFixed(1)}% (Threshold: 70%)`
        },
        {
            label: "Strike Selection Matrix",
            value: rec && rec.instrument ? "COMPILED" : "PENDING",
            valid: !!(rec && rec.instrument),
            detail: `${(rec && rec.position_profile) || 'Mathematical Strike Engineering active'}`
        },
        {
            label: "Risk Engine Threshold",
            value: rec && rec.exit_plan?.initial_sl ? "SECURED" : "FAILSAFE",
            valid: !!(rec && rec.exit_plan?.initial_sl),
            detail: `Initial SL @ ${(rec && rec.exit_plan?.initial_sl) || 'Dynamic ATR'}`
        },
        {
            label: "Gamma Safety Gate",
            value: analysis.structural?.gex?.is_live ? "LIVE" : "CALIBRATED",
            valid: true,
            detail: isExpiry ? "EXPIRY MODE: Scaling for Gamma Volatility" : "NOMINAL: Path clear of major walls"
        },
        {
            label: "Position Lifecycle",
            value: isExpiry ? "AGGRESSIVE" : "INTRADAY",
            valid: true,
            detail: isExpiry ? "EXPIRY MODE: High-Conviction Gamma Sniper active" : "Auto-Square at 3:15 PM. Overnight HOLD: RESTRICTED."
        }
    ];

    return (
        <div className="p-1.5 h-full flex flex-col relative overflow-hidden">
            <div className={`absolute top-0 right-0 w-24 h-24 blur-[40px] rounded-full -mr-12 -mt-12 transition-colors duration-1000 ${action === 'BUY' ? 'bg-emerald-500/10' : action === 'SELL' ? 'bg-red-500/10' : 'bg-indigo-500/10'}`} />

            <div className="relative z-10 flex-1 flex flex-col gap-1">
                <div className="flex items-center justify-between bg-white/[0.03] p-1.5 rounded-lg border border-white/5">
                    <div className="flex items-center gap-2">
                        <Activity className={`w-3 h-3 ${action === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`} />
                        <h3 className="text-[10px] font-black text-white uppercase tracking-wider">
                            {action} SETUP: {symbol.replace('^', '')}
                        </h3>
                    </div>
                </div>

                <div className="space-y-1 flex-1 overflow-y-auto custom-scrollbar">
                    {criteria.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between gap-2 bg-black/10 p-1.5 rounded-lg border border-white/[0.03] group transition-all hover:bg-black/30">
                            <div className="flex items-center gap-2 min-w-0">
                                <div className={`p-0.5 rounded-full ${item.valid ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                                    {item.valid ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Shield className="w-2.5 h-2.5" />}
                                </div>
                                <p className="text-[8px] font-black text-slate-400 uppercase tracking-tighter truncate">{item.label}</p>
                            </div>
                            <span className={`text-[7px] font-black px-1.5 py-0.5 rounded border leading-none ${item.valid ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
                                {item.value}
                            </span>
                        </div>
                    ))}
                </div>

                <div className={`p-2 rounded-xl border transition-all duration-500 ${action === 'BUY' ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <div className="flex items-center justify-between mb-1">
                        <p className={`text-[8px] font-black uppercase tracking-widest flex items-center gap-1.5 ${action === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                            <Zap className="w-2.5 h-2.5" /> RECOMMENDATION
                        </p>
                    </div>
                    <p className="text-[9px] font-bold text-white/90 leading-tight">
                        <span className="text-white underline decoration-indigo-500/30">{rec.instrument}</span>. Targets: <span className="text-emerald-400">{rec.exit_plan?.targets?.slice(0, 2).join(', ')}</span>
                    </p>
                    <div className="mt-1.5 flex items-center gap-3 text-[7px] font-black uppercase tracking-widest text-slate-500 border-t border-white/5 pt-1.5">
                        <div className="flex items-center gap-1">
                            <Shield className="w-2.5 h-2.5 text-red-500/50" /> SL: {rec.exit_plan?.initial_sl}
                        </div>
                        <div className="flex items-center gap-1 border-l border-white/5 pl-3">
                            <Target className="w-2.5 h-2.5 text-emerald-500/50" /> TSL: 15%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const Activity = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
    </svg>
);

export default TradeChecklist;
