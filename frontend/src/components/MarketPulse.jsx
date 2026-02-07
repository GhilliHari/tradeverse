import React from 'react';
import {
    TrendingUp, TrendingDown, Activity, DollarSign, Users,
    BarChart3, Flame, Snowflake, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, PieChart, Pie, Tooltip } from 'recharts';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- MARKET PULSE DATA ---

// Market Breadth
const breadthData = {
    advances: 1247,
    declines: 892,
    unchanged: 156,
    advanceDeclineRatio: 1.40
};

// Sector Performance (% change today)
const sectorData = [
    { sector: 'Bank', change: 1.8, color: '#10b981' },
    { sector: 'IT', change: -0.5, color: '#ef4444' },
    { sector: 'Auto', change: 2.1, color: '#10b981' },
    { sector: 'Pharma', change: -1.2, color: '#ef4444' },
    { sector: 'Metal', change: 0.8, color: '#10b981' },
    { sector: 'Energy', change: -0.3, color: '#ef4444' },
    { sector: 'FMCG', change: 0.4, color: '#10b981' },
    { sector: 'Realty', change: 3.2, color: '#10b981' }
];

// Top Movers
const topGainers = [
    { symbol: 'HDFC Bank', change: 2.8, price: '1,645.50', volume: '12.4M' },
    { symbol: 'ICICI Bank', change: 2.3, price: '1,089.20', volume: '8.7M' },
    { symbol: 'Axis Bank', change: 1.9, price: '1,124.80', volume: '5.2M' }
];

const topLosers = [
    { symbol: 'IndusInd Bank', change: -1.8, price: '1,456.30', volume: '3.1M' },
    { symbol: 'Bandhan Bank', change: -1.5, price: '234.60', volume: '2.8M' },
    { symbol: 'IDFC First', change: -1.2, price: '78.45', volume: '4.5M' }
];

// FII/DII Activity
const institutionalData = [
    { name: 'FII', buy: 4250, sell: 3890, net: 360 },
    { name: 'DII', buy: 3120, sell: 3450, net: -330 }
];

// Market Heatmap (simplified)
const heatmapData = [
    { name: 'Large Cap', value: 65, sentiment: 'bullish' },
    { name: 'Mid Cap', value: 25, sentiment: 'neutral' },
    { name: 'Small Cap', value: 10, sentiment: 'bearish' }
];

const StockRow = ({ stock, isGainer }) => (
    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
        <div className="flex-1">
            <div className="font-bold text-white text-sm">{stock.symbol}</div>
            <div className="text-[10px] text-slate-500 font-mono">Vol: {stock.volume}</div>
        </div>
        <div className="text-right">
            <div className="font-mono text-sm text-slate-300">₹{stock.price}</div>
            <div className={`text-xs font-bold flex items-center justify-end gap-1 ${isGainer ? 'text-emerald-400' : 'text-red-400'}`}>
                {isGainer ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {Math.abs(stock.change)}%
            </div>
        </div>
    </div>
);

const MarketPulse = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">

            {/* Header Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Advances</span>
                    </div>
                    <div className="text-3xl font-black text-emerald-400 font-mono">{breadthData.advances}</div>
                </div>

                <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingDown className="w-4 h-4 text-red-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Declines</span>
                    </div>
                    <div className="text-3xl font-black text-red-400 font-mono">{breadthData.declines}</div>
                </div>

                <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-purple-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">A/D Ratio</span>
                    </div>
                    <div className="text-3xl font-black text-purple-400 font-mono">{breadthData.advanceDeclineRatio}</div>
                </div>

                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Users className="w-4 h-4 text-cyan-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">FII Net</span>
                    </div>
                    <div className="text-3xl font-black text-cyan-400 font-mono">+₹360Cr</div>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Sector Performance */}
                <HUDCard title="SECTOR HEAT MAP" neonColor="amber" className="lg:col-span-2 h-[400px]">
                    <div className="p-6 h-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={sectorData} layout="horizontal">
                                <XAxis type="number" domain={[-2, 4]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis dataKey="sector" type="category" tick={{ fill: '#cbd5e1', fontSize: 11, fontWeight: 'bold' }} width={60} axisLine={false} tickLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                                    formatter={(value) => [`${value}%`, 'Change']}
                                />
                                <Bar dataKey="change" radius={[0, 4, 4, 0]}>
                                    {sectorData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </HUDCard>

                {/* FII/DII Activity */}
                <HUDCard title="INSTITUTIONAL FLOW" neonColor="indigo" className="h-[400px]">
                    <div className="p-6 space-y-6">
                        {institutionalData.map(inst => (
                            <div key={inst.name} className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-black text-white">{inst.name}</span>
                                    <span className={`text-lg font-mono font-bold ${inst.net > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {inst.net > 0 ? '+' : ''}{inst.net} Cr
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                        <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Buy</div>
                                        <div className="text-sm font-mono font-bold text-emerald-400">₹{inst.buy}</div>
                                    </div>
                                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                        <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Sell</div>
                                        <div className="text-sm font-mono font-bold text-red-400">₹{inst.sell}</div>
                                    </div>
                                </div>
                            </div>
                        ))}

                        <div className="pt-4 border-t border-white/10">
                            <div className="text-[10px] text-slate-500 font-bold uppercase mb-2">Market Cap Distribution</div>
                            <div className="space-y-2">
                                {heatmapData.map(item => (
                                    <div key={item.name} className="flex items-center justify-between">
                                        <span className="text-xs text-slate-300">{item.name}</span>
                                        <div className="flex items-center gap-2">
                                            <div className="w-20 h-2 bg-white/5 rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${item.sentiment === 'bullish' ? 'bg-emerald-500' : item.sentiment === 'bearish' ? 'bg-red-500' : 'bg-slate-500'}`}
                                                    style={{ width: `${item.value}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-mono text-slate-400">{item.value}%</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </HUDCard>
            </div>

            {/* Top Movers */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <HUDCard title="TOP GAINERS (BANK NIFTY)" neonColor="emerald" className="h-[300px]">
                    <div className="p-6 space-y-3">
                        {topGainers.map(stock => (
                            <StockRow key={stock.symbol} stock={stock} isGainer={true} />
                        ))}
                    </div>
                </HUDCard>

                <HUDCard title="TOP LOSERS (BANK NIFTY)" neonColor="red" className="h-[300px]">
                    <div className="p-6 space-y-3">
                        {topLosers.map(stock => (
                            <StockRow key={stock.symbol} stock={stock} isGainer={false} />
                        ))}
                    </div>
                </HUDCard>
            </div>
        </div>
    );
};

export default MarketPulse;
