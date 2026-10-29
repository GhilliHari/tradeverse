import React from 'react';
import { Gauge, Zap, TrendingUp, Clock, Activity } from 'lucide-react';

const GreeksCheatSheet = ({ data, compact = false }) => {
    // Simulated Greeks if not provided by data
    const greeks = data?.greeks || {
        delta: 0.52,
        gamma: 0.004,
        theta: -12.5,
        vega: 45.2,
        iv: 14.8
    };

    const greekItems = [
        {
            label: "DELTA",
            value: greeks.delta?.toFixed(2),
            desc: "Speed vs Spot",
            icon: TrendingUp,
            color: "text-emerald-400",
            bg: "bg-emerald-500/10",
            meaning: "1pt BN move = ₹" + (greeks.delta * 100).toFixed(0) + " Premium move"
        },
        {
            label: "GAMMA",
            value: greeks.gamma?.toFixed(4),
            desc: "Acceleration",
            icon: Zap,
            color: "text-indigo-400",
            bg: "bg-indigo-500/10",
            meaning: "Explosiveness of Delta (High = Fast Profit)"
        },
        {
            label: "THETA",
            value: greeks.theta?.toFixed(1),
            desc: "Time Decay",
            icon: Clock,
            color: "text-rose-400",
            bg: "bg-rose-500/10",
            meaning: "Daily loss due to time (Avoid flat markets)"
        },
        {
            label: "VEGA",
            value: greeks.vega?.toFixed(1),
            desc: "Volatility",
            icon: Activity,
            color: "text-purple-400",
            bg: "bg-purple-500/10",
            meaning: "Sensitivity to Market Fear (IV)"
        }
    ];

    if (compact) {
        return (
            <div className="p-1.5 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar h-full w-full">
                {greekItems.map((item, idx) => (
                    <div key={idx} className={`px-2 py-1 rounded-lg border border-white/5 flex items-center gap-2 ${item.color} ${item.bg} w-full flex-1 justify-center whitespace-nowrap`}>
                        <span className="text-[8px] font-black uppercase tracking-widest opacity-80">{item.label}</span>
                        <span className="text-[10px] font-mono tabular-nums font-black">{item.value}</span>
                    </div>
                ))}
                <div className={`px-2 py-1 rounded-lg border border-white/5 flex items-center gap-2 text-amber-400 bg-amber-500/10 w-full flex-1 justify-center whitespace-nowrap`}>
                    <span className="text-[8px] font-black uppercase tracking-widest opacity-80">IV</span>
                    <span className="text-[10px] font-mono tabular-nums font-black">{greeks.iv}%</span>
                </div>
            </div>
        );
    }

    return (
        <div className="p-4 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-4 bg-indigo-500/5 p-2 rounded-xl border border-indigo-500/10">
                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                    <Gauge className="w-4 h-4" />
                </div>
                <div>
                    <h3 className="text-[10px] font-black text-white uppercase tracking-wider italic">Greeks Dashboard</h3>
                    <p className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Real-time Sensitivity</p>
                </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 flex-1 min-h-0 overflow-hidden">
                {greekItems.map((item, idx) => (
                    <div key={idx} className="glass-panel p-2 rounded-xl border border-white/5 flex flex-col justify-between group hover:border-white/10 transition-all relative overflow-hidden">
                        <div className="flex justify-between items-start">
                            <div className={`p-1 rounded-lg ${item.bg} ${item.color}`}>
                                <item.icon className="w-3 h-3" />
                            </div>
                            <span className={`text-[10px] font-black tabular-nums ${item.color}`}>{item.value}</span>
                        </div>
                        <div className="mt-1">
                            <p className="text-[8px] font-black text-white uppercase tracking-tighter leading-none">{item.label}</p>
                            <p className="text-[6px] font-bold text-slate-500 uppercase tracking-widest leading-none mt-0.5 truncate">{item.desc}</p>
                        </div>

                        {/* Tooltip on Hover - More compact */}
                        <div className="absolute inset-0 bg-slate-900/95 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center p-1.5 text-center rounded-xl z-20">
                            <p className="text-[7px] font-black text-white uppercase tracking-tighter leading-tight">
                                {item.meaning}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-2 p-2 bg-white/[0.02] rounded-lg border border-white/5 flex items-center justify-between">
                <div>
                    <span className="text-[6px] font-black text-slate-500 uppercase tracking-widest block mb-0.5 leading-none">Implied Volatility</span>
                    <span className="text-xs font-black text-amber-400 tabular-nums">{greeks.iv}%</span>
                </div>
                <div className="text-right">
                    <span className="text-[6px] font-black text-slate-500 uppercase tracking-widest block mb-0.5 leading-none">IV Percentile</span>
                    <span className="text-[8px] font-black text-slate-300">MEDIUM (42nd)</span>
                </div>
            </div>
        </div>
    );
};

const Tracking = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <path d="m3 11 18-5v12L3 11Z"></path>
        <path d="M11.6 8v6"></path>
    </svg>
);

export default GreeksCheatSheet;
