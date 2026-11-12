import React, { useState, useEffect, useCallback } from 'react';
import {
    Wallet, TrendingUp, DollarSign,
    Clock, ArrowUpRight, ArrowDownRight, RefreshCw, Cloud, Shield
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import HUDCard from './ui/HUDCard';
import { API_URL } from '../config/api';

const HoldingRow = ({ holding }) => {
    const isProfitable = holding.pnl >= 0;

    return (
        <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-white">{holding.symbol}</h4>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${holding.isOpen ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'}`}>
                            {holding.isOpen ? 'OPEN POSITION' : 'CLOSED'}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400">
                            {holding.exchange || 'NFO'}
                        </span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                        Net Qty: {holding.qty} | Entry Avg: ₹{Number(holding.avgPrice || 0).toFixed(2)} | SL: {holding.stopLossPct}% | Target: +{holding.targetPct}%
                    </div>
                </div>
                <div className="text-right">
                    <div className="font-mono text-lg font-bold text-white">LTP: ₹{Number(holding.ltp || 0).toFixed(2)}</div>
                    <div className={`text-xs font-bold flex items-center justify-end gap-1 ${isProfitable ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isProfitable ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {holding.pnlPercent >= 0 ? '+' : ''}{Number(holding.pnlPercent || 0).toFixed(2)}%
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-3 pt-3 border-t border-white/10">
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Exposure</div>
                    <div className="text-sm font-mono text-slate-300">₹{Number(holding.invested || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Current Value</div>
                    <div className="text-sm font-mono text-slate-300">₹{Number(holding.current || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Live P&L</div>
                    <div className={`text-sm font-mono font-bold ${isProfitable ? 'text-emerald-400' : 'text-red-400'}`}>
                        {isProfitable ? '+' : ''}₹{Number(holding.pnl || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                </div>
            </div>
        </div>
    );
};

const Portfolio = () => {
    const [positions, setPositions] = useState([]);
    const [funds, setFunds] = useState({ availablecash: 0, net: 0, utiliseddebits: 0, max_position_size: 10000, daily_loss_limit: 1000 });
    const [risk, setRisk] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    const fetchLivePortfolio = useCallback(async () => {
        setIsLoading(true);
        try {
            const [posRes, fundsRes] = await Promise.all([
                fetch(`${API_URL}/api/broker/positions`).catch(() => null),
                fetch(`${API_URL}/api/broker/funds`).catch(() => null)
            ]);

            if (posRes && posRes.ok) {
                const posData = await posRes.json();
                if (posData && Array.isArray(posData.positions)) {
                    const mapped = posData.positions.map(p => {
                        const qty = Number(p.netqty || 0);
                        const avg = Number(p.buyavgprice || p.sellavgprice || 0);
                        const ltp = Number(p.ltp || avg || 0);
                        const absQty = Math.abs(qty) || 15;
                        const invested = avg * absQty;
                        const current = ltp * absQty;
                        const pnl = Number(p.pnl || 0);
                        const pnlPercent = invested > 0 ? (pnl / invested) * 100 : 0;
                        return {
                            symbol: p.tradingsymbol,
                            exchange: p.exchange || 'NFO',
                            qty: qty,
                            avgPrice: avg,
                            ltp: ltp,
                            invested: invested,
                            current: current,
                            pnl: pnl,
                            pnlPercent: pnlPercent,
                            isOpen: qty !== 0,
                            stopLossPct: p.stop_loss_pct ?? -15,
                            targetPct: p.target_pct ?? 25
                        };
                    });
                    setPositions(mapped);
                }
            }

            if (fundsRes && fundsRes.ok) {
                const fData = await fundsRes.json();
                setFunds(fData);
                if (fData.risk) setRisk(fData.risk);
            }
        } catch (err) {
            console.error('Error loading live Angel One portfolio:', err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLivePortfolio();
        const interval = setInterval(fetchLivePortfolio, 8000);
        return () => clearInterval(interval);
    }, [fetchLivePortfolio]);

    const availableCash = Number(funds.availablecash || 0);
    const utilisedMargin = Number(funds.utiliseddebits || 0);
    const totalPnL = positions.reduce((s, p) => s + (Number(p.pnl) || 0), 0);
    const openPositionsCount = positions.filter(p => p.isOpen).length;

    const allocationData = [
        { name: 'Available Cash', value: Math.max(1, availableCash), color: '#10b981' },
        { name: 'Utilised Margin', value: Math.max(0, utilisedMargin), color: '#6366f1' }
    ];

    const riskMetrics = [
        { metric: 'Max Position Size Cap', value: `₹${Number(funds.max_position_size || 10000).toLocaleString('en-IN')}`, status: 'excellent' },
        { metric: 'Daily Loss Limit', value: `₹${Number(funds.daily_loss_limit || 1000).toLocaleString('en-IN')}`, status: 'excellent' },
        { metric: 'Remaining Loss Buffer', value: `₹${Number(risk.remaining_loss_allowance ?? 1000).toLocaleString('en-IN')}`, status: 'good' },
        { metric: 'Circuit Breaker Status', value: risk.circuit_breaker_status || 'NOMINAL', status: (risk.circuit_breaker_status || 'NOMINAL') === 'NOMINAL' ? 'excellent' : 'moderate' }
    ];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* Top Cloud & Broker Banner */}
            <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <Cloud className="w-5 h-5 text-indigo-400" />
                    <div>
                        <div className="text-xs font-black uppercase tracking-wider text-indigo-400">
                            Angel One Live RMS Portfolio & Margin Telemetry
                        </div>
                        <div className="text-[11px] text-slate-300 font-mono">
                            Auto-Stop-Loss (-15%), Target (+25%), 15m Time-Exit & 15:20 IST EOD Square-Off Active in Cloud
                        </div>
                    </div>
                </div>
                <button
                    onClick={fetchLivePortfolio}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2"
                >
                    <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                    Sync Angel One RMS
                </button>
            </div>

            {/* Portfolio Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Wallet className="w-4 h-4 text-emerald-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Available Cash</span>
                    </div>
                    <div className="text-2xl font-black text-white font-mono">
                        ₹{availableCash.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-emerald-400 mt-1">Angel One RMS Live Balance</div>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Shield className="w-4 h-4 text-indigo-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Utilised Margin</span>
                    </div>
                    <div className="text-2xl font-black text-indigo-400 font-mono">
                        ₹{utilisedMargin.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Open Positions: {openPositionsCount} / 1</div>
                </div>

                <div className={`p-4 rounded-2xl ${totalPnL >= 0 ? 'bg-cyan-500/10 border-cyan-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className={`w-4 h-4 ${totalPnL >= 0 ? 'text-cyan-400' : 'text-red-400'}`} />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Today's Live P&L</span>
                    </div>
                    <div className={`text-2xl font-black font-mono ${totalPnL >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                        {totalPnL >= 0 ? '+' : ''}₹{totalPnL.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">Realized + Unrealized</div>
                </div>

                <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="w-4 h-4 text-purple-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Position Cap</span>
                    </div>
                    <div className="text-2xl font-black text-purple-400 font-mono">
                        ₹{Number(funds.max_position_size || 10000).toLocaleString('en-IN')}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">Daily Loss Limit: ₹{Number(funds.daily_loss_limit || 1000).toLocaleString('en-IN')}</div>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Positions List */}
                <div className="lg:col-span-2 space-y-4">
                    <HUDCard title="LIVE ANGEL ONE POSITIONS" neonColor="indigo">
                        <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                            {positions.length === 0 ? (
                                <div className="p-10 text-center rounded-xl bg-white/5 border border-white/5">
                                    <div className="text-sm font-bold text-slate-300 mb-1">No Open Angel One Positions Right Now</div>
                                    <div className="text-xs text-slate-500 font-mono">
                                        Available Cash ₹{availableCash.toLocaleString('en-IN', { minimumFractionDigits: 2 })} is protected and ready for the next high-conviction signal.
                                    </div>
                                </div>
                            ) : (
                                positions.map((holding, idx) => (
                                    <HoldingRow key={holding.symbol || idx} holding={holding} />
                                ))
                            )}
                        </div>
                    </HUDCard>
                </div>

                {/* Sidebar - Allocation & Risk */}
                <div className="space-y-6">
                    <HUDCard title="CAPITAL ALLOCATION" neonColor="purple" className="h-[280px]">
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
                                            formatter={(value) => `₹${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
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
                                        <span className="text-xs font-mono text-slate-400">
                                            ₹{Number(item.value === 1 && availableCash === 0 ? 0 : item.value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </HUDCard>

                    <HUDCard title="RISK GUARDRAILS" neonColor="amber" className="h-[280px]">
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
        </div>
    );
};

export default Portfolio;
