import React from 'react';
import {
    Briefcase, TrendingUp, Shield, Zap, AlertTriangle,
    PieChart as PieChartIcon, ArrowRight, Check
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- MOCK DATA FOR BASKETS ---

const mockSparkline = Array.from({ length: 20 }, (_, i) => ({
    value: 100 + i * 2 + Math.random() * 20
}));

const baskets = [
    {
        id: 'bank-titans',
        title: 'Banking Titans',
        description: 'The heavyweights moving the Nifty Bank Index. Low volatility, stable long-term growth.',
        cagr: '18.4%',
        risk: 'LOW',
        minAmount: '₹15,400',
        constituents: ['HDFC Bank', 'ICICI Bank', 'SBI', 'Kotak Bank'],
        color: 'emerald',
        icon: Shield
    },
    {
        id: 'psu-momentum',
        title: 'PSU Bank Momentum',
        description: 'High-beta Public Sector Banks capturing aggressive government capex cycles.',
        cagr: '42.8%',
        risk: 'HIGH',
        minAmount: '₹4,800',
        constituents: ['Punjab National Bank', 'Bank of Baroda', 'Canara Bank', 'Union Bank'],
        color: 'amber',
        icon: Zap
    },
    {
        id: 'fintech-disruptors',
        title: 'Fintech & NBFC',
        description: 'New-age financial services and non-banking lenders leveraging technology.',
        cagr: '28.1%',
        risk: 'MED',
        minAmount: '₹8,200',
        constituents: ['Bajaj Finance', 'Jio Financial', 'Paytm', 'Angel One'],
        color: 'cyan',
        icon: Briefcase
    },
    {
        id: 'volatility-hedge',
        title: 'Volatility Hedge',
        description: 'Defensive assets to park capital during high VIX / Market Crashes.',
        cagr: '11.2%',
        risk: 'LOW',
        minAmount: '₹2,500',
        constituents: ['Gold BeES', 'Liquid BeES', 'Silver BeES'],
        color: 'purple',
        icon: AlertTriangle
    }
];

const SmallcaseCard = ({ basket }) => {
    const Icon = basket.icon;
    const colorClass = basket.color === 'emerald' ? 'text-emerald-400' :
        basket.color === 'amber' ? 'text-amber-400' :
            basket.color === 'cyan' ? 'text-cyan-400' : 'text-purple-400';

    const bgClass = basket.color === 'emerald' ? 'bg-emerald-500/10 border-emerald-500/20' :
        basket.color === 'amber' ? 'bg-amber-500/10 border-amber-500/20' :
            basket.color === 'cyan' ? 'bg-cyan-500/10 border-cyan-500/20' : 'bg-purple-500/10 border-purple-500/20';

    return (
        <div className={`p-6 rounded-2xl border ${bgClass} hover:bg-opacity-20 transition-all group relative overflow-hidden backdrop-blur-sm`}>
            {/* Hover Glow */}
            <div className={`absolute -right-20 -top-20 w-40 h-40 rounded-full blur-[80px] opacity-20 group-hover:opacity-40 transition-opacity bg-${basket.color}-500 pointer-events-none`} />

            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl bg-black/40 border border-white/5 ${colorClass}`}>
                    <Icon className="w-6 h-6" />
                </div>
                <div className={`text-[10px] font-black px-2 py-1 rounded uppercase tracking-widest bg-black/40 border border-white/5 ${colorClass}`}>
                    {basket.risk} RISK
                </div>
            </div>

            <h3 className="text-xl font-black text-white mb-2">{basket.title}</h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6 min-h-[40px]">
                {basket.description}
            </p>

            <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">3Y CAGR</div>
                    <div className="text-lg font-mono font-bold text-white flex items-center gap-1">
                        <TrendingUp className="w-3 h-3 text-emerald-400" />
                        {basket.cagr}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase">Min. Amount</div>
                    <div className="text-lg font-mono font-bold text-white">
                        {basket.minAmount}
                    </div>
                </div>
            </div>

            {/* Sparkline */}
            <div className="h-16 w-full mb-6">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={mockSparkline}>
                        <defs>
                            <linearGradient id={`grad-${basket.id}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor={basket.color === 'emerald' ? '#10b981' : basket.color === 'amber' ? '#f59e0b' : basket.color === 'cyan' ? '#06b6d4' : '#a855f7'} stopOpacity={0.4} />
                                <stop offset="100%" stopColor="#000" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={basket.color === 'emerald' ? '#10b981' : basket.color === 'amber' ? '#f59e0b' : basket.color === 'cyan' ? '#06b6d4' : '#a855f7'}
                            fill={`url(#grad-${basket.id})`}
                            strokeWidth={2}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Constituents */}
            <div className="flex flex-wrap gap-2 mb-6">
                {basket.constituents.map(stock => (
                    <span key={stock} className="text-[10px] font-bold px-2 py-1 rounded-full bg-white/5 text-slate-300 border border-white/5">
                        {stock}
                    </span>
                ))}
            </div>

            <button className={`w-full py-3 rounded-xl font-black text-sm uppercase tracking-widest transition-all
                ${basket.color === 'emerald' ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/20' :
                    basket.color === 'amber' ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/20' :
                        basket.color === 'cyan' ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-900/20' :
                            'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-900/20'
                } flex items-center justify-center gap-2 group-hover:scale-[1.02] active:scale-[0.98]`}>
                Invest Now <ArrowRight className="w-4 h-4" />
            </button>
        </div>
    );
};

const Smallcases = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
                        <Briefcase className="w-6 h-6 text-emerald-400" />
                        AI-CURATED BASKETS
                    </h2>
                    <p className="text-sm text-slate-400 mt-1 font-medium">
                        Thematic portfolios generated by Cortex for long-term wealth creation.
                    </p>
                </div>
                <div className="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Rebalanced Monthly</span>
                </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {baskets.map(basket => (
                    <SmallcaseCard key={basket.id} basket={basket} />
                ))}
            </div>

            {/* Footer Insight */}
            <HUDCard title="BASKET ANALYTICS" neonColor="emerald" className="mt-8">
                <div className="p-6 flex items-center justify-between">
                    <div>
                        <h4 className="text-lg font-bold text-white">Why Smallcases?</h4>
                        <p className="text-sm text-slate-400 max-w-2xl mt-1">
                            While F&O generates daily cash flow, Smallcases build long-term equity.
                            Our AI suggests allocating <span className="text-emerald-400 font-bold">20% of F&O profits</span> automatically into "Banking Titans"
                            to compound wealth safely.
                        </p>
                    </div>
                    <button className="px-6 py-2 rounded-lg border border-white/10 hover:bg-white/5 text-xs font-bold text-white uppercase tracking-widest transition-all">
                        Configure Auto-Sweep
                    </button>
                </div>
            </HUDCard>
        </div>
    );
};

export default Smallcases;
