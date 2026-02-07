import React from 'react';
import {
    Wallet, TrendingUp, TrendingDown, DollarSign, PieChart as PieChartIcon,
    Shield, AlertCircle, Clock, Target, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- PORTFOLIO DATA ---

// Current Holdings
const holdings = [
    {
        symbol: 'HDFC Bank',
        type: 'EQUITY',
        qty: 50,
        avgPrice: 1580.20,
        ltp: 1645.50,
        invested: 79010,
        current: 82275,
        pnl: 3265,
        pnlPercent: 4.13,
        dayChange: 2.8
    },
    {
        symbol: 'BankNifty 48200 CE',
        type: 'CALL',
        qty: 50,
        avgPrice: 245.00,
        ltp: 312.50,
        invested: 12250,
        current: 15625,
        pnl: 3375,
        pnlPercent: 27.55,
        dayChange: 8.2,
        expiry: '30-Jan-2026'
    },
    {
        symbol: 'BankNifty 47800 PE',
        type: 'PUT',
        qty: 50,
        avgPrice: 180.00,
        ltp: 125.00,
        invested: 9000,
        current: 6250,
        pnl: -2750,
        pnlPercent: -30.56,
        dayChange: -12.5,
        expiry: '30-Jan-2026'
    },
    {
        symbol: 'ICICI Bank',
        type: 'EQUITY',
        qty: 30,
        avgPrice: 1065.00,
        ltp: 1089.20,
        invested: 31950,
        current: 32676,
        pnl: 726,
        pnlPercent: 2.27,
        dayChange: 2.3
    }
];

// Portfolio Summary
const portfolioSummary = {
    totalInvested: 132210,
    currentValue: 136826,
    totalPnL: 4616,
    totalPnLPercent: 3.49,
    realizedPnL: 12450,
    unrealizedPnL: 4616,
    dayPnL: 2840,
    dayPnLPercent: 2.12
};

// Asset Allocation
const allocationData = [
    { name: 'Equity', value: 114951, color: '#6366f1', percent: 84 },
    { name: 'F&O', value: 21875, color: '#f59e0b', percent: 16 }
];

// Risk Metrics
const riskMetrics = [
    { metric: 'Portfolio Beta', value: '1.15', status: 'moderate' },
    { metric: 'Max Drawdown', value: '-4.2%', status: 'good' },
    { metric: 'Sharpe Ratio', value: '2.84', status: 'excellent' },
    { metric: 'Options Exposure', value: '16%', status: 'moderate' }
];

// Daily P&L History (last 7 days)
const dailyPnLData = [
    { day: 'Mon', pnl: 1200 },
    { day: 'Tue', pnl: -800 },
    { day: 'Wed', pnl: 2400 },
    { day: 'Thu', pnl: 1800 },
    { day: 'Fri', pnl: -600 },
    { day: 'Sat', pnl: 0 },
    { day: 'Today', pnl: 2840 }
];

const HoldingRow = ({ holding }) => {
    const isProfitable = holding.pnl >= 0;

    return (
        <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-white">{holding.symbol}</h4>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${holding.type === 'EQUITY' ? 'bg-indigo-500/20 text-indigo-400' :
                                holding.type === 'CALL' ? 'bg-emerald-500/20 text-emerald-400' :
                                    'bg-red-500/20 text-red-400'
                            }`}>
                            {holding.type}
                        </span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">
                        Qty: {holding.qty} | Avg: ₹{holding.avgPrice.toFixed(2)}
                        {holding.expiry && ` | Exp: ${holding.expiry}`}
                    </div>
                </div>
                <div className="text-right">
                    <div className="font-mono text-lg font-bold text-white">₹{holding.ltp.toFixed(2)}</div>
                    <div className={`text-xs font-bold flex items-center justify-end gap-1 ${holding.dayChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {holding.dayChange >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {Math.abs(holding.dayChange)}%
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-3 border-t border-white/10">
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Invested</div>
                    <div className="text-sm font-mono text-slate-300">₹{holding.invested.toLocaleString()}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Current</div>
                    <div className="text-sm font-mono text-slate-300">₹{holding.current.toLocaleString()}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">P&L</div>
                    <div className={`text-sm font-mono font-bold ${isProfitable ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isProfitable ? '+' : ''}₹{holding.pnl.toLocaleString()} ({holding.pnlPercent.toFixed(2)}%)
                    </div>
                </div>
            </div>
        </div>
    );
};

const Portfolio = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">

            {/* Portfolio Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Wallet className="w-4 h-4 text-indigo-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Total Value</span>
                    </div>
                    <div className="text-2xl font-black text-white font-mono">₹{(portfolioSummary.currentValue / 1000).toFixed(1)}K</div>
                    <div className="text-[10px] text-slate-500 mt-1">Invested: ₹{(portfolioSummary.totalInvested / 1000).toFixed(1)}K</div>
                </div>

                <div className={`p-4 rounded-2xl ${portfolioSummary.totalPnL >= 0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className={`w-4 h-4 ${portfolioSummary.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Total P&L</span>
                    </div>
                    <div className={`text-2xl font-black font-mono ${portfolioSummary.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {portfolioSummary.totalPnL >= 0 ? '+' : ''}₹{(portfolioSummary.totalPnL / 1000).toFixed(1)}K
                    </div>
                    <div className={`text-[10px] mt-1 ${portfolioSummary.totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {portfolioSummary.totalPnLPercent >= 0 ? '+' : ''}{portfolioSummary.totalPnLPercent}%
                    </div>
                </div>

                <div className={`p-4 rounded-2xl ${portfolioSummary.dayPnL >= 0 ? 'bg-cyan-500/10 border-cyan-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className={`w-4 h-4 ${portfolioSummary.dayPnL >= 0 ? 'text-cyan-400' : 'text-red-400'}`} />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Today's P&L</span>
                    </div>
                    <div className={`text-2xl font-black font-mono ${portfolioSummary.dayPnL >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                        {portfolioSummary.dayPnL >= 0 ? '+' : ''}₹{(portfolioSummary.dayPnL / 1000).toFixed(1)}K
                    </div>
                    <div className={`text-[10px] mt-1 ${portfolioSummary.dayPnL >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                        {portfolioSummary.dayPnLPercent >= 0 ? '+' : ''}{portfolioSummary.dayPnLPercent}%
                    </div>
                </div>

                <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="w-4 h-4 text-purple-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Realized</span>
                    </div>
                    <div className="text-2xl font-black text-purple-400 font-mono">₹{(portfolioSummary.realizedPnL / 1000).toFixed(1)}K</div>
                    <div className="text-[10px] text-slate-500 mt-1">Closed Positions</div>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Holdings List */}
                <div className="lg:col-span-2 space-y-4">
                    <HUDCard title="CURRENT HOLDINGS" neonColor="indigo">
                        <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                            {holdings.map((holding, idx) => (
                                <HoldingRow key={idx} holding={holding} />
                            ))}
                        </div>
                    </HUDCard>
                </div>

                {/* Sidebar - Allocation & Risk */}
                <div className="space-y-6">
                    {/* Asset Allocation */}
                    <HUDCard title="ALLOCATION" neonColor="purple" className="h-[280px]">
                        <div className="p-6 h-full flex flex-col">
                            <div className="flex-1 relative">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={allocationData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={50}
                                            outerRadius={70}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {allocationData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            formatter={(value) => `₹${(value / 1000).toFixed(1)}K`}
                                            contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="space-y-2 mt-4">
                                {allocationData.map(item => (
                                    <div key={item.name} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                            <span className="text-xs text-slate-300 font-bold">{item.name}</span>
                                        </div>
                                        <span className="text-xs font-mono text-slate-400">{item.percent}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </HUDCard>

                    {/* Risk Metrics */}
                    <HUDCard title="RISK METRICS" neonColor="amber" className="h-[280px]">
                        <div className="p-6 space-y-4">
                            {riskMetrics.map((metric, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                                    <div>
                                        <div className="text-xs text-slate-400">{metric.metric}</div>
                                        <div className="text-sm font-bold text-white font-mono mt-1">{metric.value}</div>
                                    </div>
                                    <div className={`w-2 h-2 rounded-full ${metric.status === 'excellent' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' :
                                            metric.status === 'good' ? 'bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]' :
                                                'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]'
                                        }`} />
                                </div>
                            ))}
                        </div>
                    </HUDCard>
                </div>
            </div>

            {/* Daily P&L Chart */}
            <HUDCard title="7-DAY P&L TREND" neonColor="cyan" className="h-[250px]">
                <div className="p-6 h-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={dailyPnLData}>
                            <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip
                                formatter={(value) => [`₹${value}`, 'P&L']}
                                contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                            />
                            <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                                {dailyPnLData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#10b981' : '#ef4444'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </HUDCard>
        </div>
    );
};

export default Portfolio;
