import React from 'react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    BarChart, Bar, Cell, PieChart, Pie, ComposedChart, Line, Legend, ReferenceLine
} from 'recharts';
import {
    TrendingUp, Activity, ArrowUpRight, ArrowDownRight,
    Calendar, DollarSign, Percent, Target, BarChart2, Layers
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- MOCK DATA GENERATION ---

// 1. Portfolio Equity Data
const equityData = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    value: 100000 + (Math.random() * 50000 - 10000) + (i * 2000)
}));

// 2. Monthly Returns
const monthlyData = [
    { month: 'Jan', ret: 4.2 }, { month: 'Feb', ret: -1.5 },
    { month: 'Mar', ret: 8.4 }, { month: 'Apr', ret: 3.1 },
    { month: 'May', ret: 5.6 }, { month: 'Jun', ret: -2.1 },
    { month: 'Jul', ret: 6.8 }, { month: 'Aug', ret: 9.2 }
];

// 3. Asset Allocation
const allocationData = [
    { name: 'Nifty Bank', value: 45, color: '#6366f1' },
    { name: 'Nifty 50', value: 30, color: '#10b981' },
    { name: 'USDINR', value: 15, color: '#f59e0b' },
    { name: 'Cash', value: 10, color: '#64748b' }
];

// 4. Intraday PCR vs Price (Dual Axis)
const pcrData = Array.from({ length: 20 }, (_, i) => {
    const time = `${9 + Math.floor(i / 4)}:${(i % 4) * 15 || '00'}`;
    const priceBase = 48000 + (Math.sin(i / 3) * 200);
    const pcrBase = 0.8 + (Math.cos(i / 3) * 0.4); // Inverse correlation roughly
    return {
        time,
        price: priceBase + Math.random() * 50,
        pcr: parseFloat((pcrBase + Math.random() * 0.1).toFixed(2))
    };
});

// 5. Open Interest Structure (Strikes)
const strikes = [47500, 47600, 47700, 47800, 47900, 48000, 48100, 48200, 48300, 48400, 48500];
const oiData = strikes.map(strike => {
    // Peak OI around 48000 (ATM)
    const dist = Math.abs(strike - 48000) / 100;
    const baseOI = 100000 * Math.exp(-0.2 * dist);
    return {
        strike,
        callOI: baseOI * (strike > 48000 ? 1.2 : 0.8) + Math.random() * 20000,
        putOI: baseOI * (strike < 48000 ? 1.2 : 0.8) + Math.random() * 20000,
    };
});

const StatCard = ({ label, value, subtext, trend, color = "white" }) => (
    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex flex-col justify-between h-full">
        <div className="flex justify-between items-start mb-2">
            <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">{label}</span>
            {trend && (
                <span className={`flex items-center text-[10px] font-bold ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                    {Math.abs(trend)}%
                </span>
            )}
        </div>
        <div>
            <div className={`text-2xl font-black text-${color} font-mono tracking-tight`}>{value}</div>
            <div className="text-[10px] text-slate-500 font-bold mt-1 max-w-[120px] leading-tight">{subtext}</div>
        </div>
    </div>
);

const Analytics = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* KPI Header - Specialized for F&O */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <StatCard
                    label="Current PCR"
                    value="0.84"
                    subtext="Bullish Divergence detected at 10:30 AM"
                    trend={5.2}
                    color="emerald-400"
                />
                <StatCard
                    label="Max Pain"
                    value="48,100"
                    subtext="Expiry Probable Range: 47900-48300"
                    trend={0.0}
                    color="amber-400"
                />
                <StatCard
                    label="Net PnL"
                    value="+₹1.45L"
                    subtext="Realized Intraday Gain"
                    trend={12.5}
                />
                <StatCard
                    label="Win Rate"
                    value="68.4%"
                    subtext="Last 30 Days"
                    trend={2.1}
                />
                <StatCard
                    label="VIX / IV"
                    value="13.2"
                    subtext="Low Volatility Regime"
                    trend={-2.5}
                />
            </div>

            {/* NEW: F&O Intelligence Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[400px]">
                {/* 1. PCR vs Price Analysis */}
                <HUDCard title="SENTIMENT: PCR vs PRICE ACTION" neonColor="cyan" className="h-full">
                    <div className="h-full w-full p-4 pt-8">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={pcrData}>
                                <defs>
                                    <linearGradient id="colorPcr" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />

                                <YAxis
                                    yAxisId="left"
                                    orientation="left"
                                    domain={['auto', 'auto']}
                                    tick={{ fontSize: 10, fill: '#cbd5e1' }}
                                    axisLine={false} tickLine={false}
                                    label={{ value: 'BankNifty Spot', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                                />
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    domain={[0.5, 1.5]}
                                    tick={{ fontSize: 10, fill: '#06b6d4' }}
                                    axisLine={false} tickLine={false}
                                    label={{ value: 'PCR', angle: 90, position: 'insideRight', fill: '#06b6d4', fontSize: 10 }}
                                />

                                <Tooltip
                                    contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                                    itemStyle={{ fontSize: '12px' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />

                                <Area
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="pcr"
                                    name="PCR (Put Call Ratio)"
                                    stroke="#06b6d4"
                                    fill="url(#colorPcr)"
                                    strokeWidth={2}
                                />
                                <Line
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="price"
                                    name="Spot Price"
                                    stroke="#e2e8f0"
                                    strokeWidth={2}
                                    dot={false}
                                />
                                <ReferenceLine yAxisId="right" y={0.7} stroke="red" strokeDasharray="3 3" label={{ position: 'right', value: 'Oversold', fill: 'red', fontSize: 10 }} />
                                <ReferenceLine yAxisId="right" y={1.2} stroke="green" strokeDasharray="3 3" label={{ position: 'right', value: 'Overbought', fill: 'green', fontSize: 10 }} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </HUDCard>

                {/* 2. Open Interest Structure */}
                <HUDCard title="OI STRUCTURE (SUPPORT/RESISTANCE)" neonColor="amber" className="h-full">
                    <div className="h-full w-full p-4 pt-8">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={oiData} layout="vertical" barGap={2}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                <YAxis
                                    dataKey="strike"
                                    type="category"
                                    tick={{ fontSize: 10, fill: '#cbd5e1', fontWeight: 'bold' }}
                                    width={50}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <Tooltip
                                    cursor={{ fill: '#ffffff10' }}
                                    contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />

                                <Bar dataKey="callOI" name="Call OI (Res)" fill="#ef4444" radius={[0, 4, 4, 0]} stackId="a" />
                                <Bar dataKey="putOI" name="Put OI (Supp)" fill="#10b981" radius={[0, 4, 4, 0]} stackId="a" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </HUDCard>
            </div>

            {/* Existing Portfolio Data (Moved Row 3) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[250px]">
                {/* Equity Curve */}
                <HUDCard title="PORTFOLIO GROWTH" neonColor="indigo" className="col-span-2 h-full">
                    <div className="h-full w-full p-4 pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={equityData}>
                                <defs>
                                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="day" hide />
                                <YAxis hide domain={['dataMin', 'dataMax']} />
                                <Tooltip contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333' }} />
                                <Area type="monotone" dataKey="value" stroke="#6366f1" fill="url(#colorValue)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </HUDCard>

                {/* Asset Allocation Pie */}
                <HUDCard title="ASSET SPLIT" neonColor="purple" className="col-span-1 h-full">
                    <div className="flex items-center justify-center h-full relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={allocationData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={60}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {allocationData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ backgroundColor: '#000000ee', borderRadius: '8px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <span className="text-xs font-black text-slate-500">DIVERSIFIED</span>
                        </div>
                    </div>
                </HUDCard>
            </div>
        </div>
    );
};

export default Analytics;
