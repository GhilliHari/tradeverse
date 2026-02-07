import React, { useState } from 'react';
import {
    Zap, Activity, TrendingUp, TrendingDown,
    Shield, Globe, Key, Clock,
    Play, Pause, Award
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

const StrategyCard = ({ strategy, onToggle }) => {
    const isActive = strategy.status === 'ACTIVE';

    return (
        <div className={`relative group p-6 rounded-3xl border transition-all duration-500 overflow-hidden ${isActive
                ? 'bg-indigo-500/10 border-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.1)]'
                : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10'
            }`}>
            {/* Background Glow */}
            {isActive && (
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-transparent opacity-50" />
            )}

            <div className="relative z-10">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-all ${isActive
                                ? 'bg-indigo-500 text-white border-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                                : 'bg-white/5 text-slate-500 border-white/10'
                            }`}>
                            {strategy.icon}
                        </div>
                        <div>
                            <h3 className={`text-lg font-black tracking-tight ${isActive ? 'text-white' : 'text-slate-300'}`}>
                                {strategy.name}
                            </h3>
                            <div className="flex items-center gap-2 mt-1">
                                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${strategy.type === 'AI HYBRID' ? 'border-purple-500/30 text-purple-400 bg-purple-500/10' :
                                        strategy.type === 'MOMENTUM' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' :
                                            'border-amber-500/30 text-amber-400 bg-amber-500/10'
                                    }`}>
                                    {strategy.type}
                                </span>
                                <span className="text-[10px] text-slate-500 font-mono">v{strategy.version}</span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={() => onToggle(strategy.id)}
                        className={`w-12 h-8 rounded-full flex items-center transition-colors p-1 ${isActive ? 'bg-indigo-500 justify-end' : 'bg-slate-700 justify-start'
                            }`}
                    >
                        <div className="w-6 h-6 rounded-full bg-white shadow-md" />
                    </button>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-1">Win Rate</div>
                        <div className={`text-sm font-black font-mono ${isActive ? 'text-emerald-400' : 'text-slate-400'}`}>
                            {strategy.winRate}%
                        </div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-1">Total PnL</div>
                        <div className={`text-sm font-black font-mono ${strategy.pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {strategy.pnl > 0 ? '+' : ''}₹{strategy.pnl.toLocaleString()}
                        </div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-1">Trades</div>
                        <div className="text-sm font-black font-mono text-slate-300">
                            {strategy.trades}
                        </div>
                    </div>
                    <div className="p-3 rounded-xl bg-black/20 border border-white/5">
                        <div className="text-[10px] font-black uppercase text-slate-500 mb-1">Sharpe</div>
                        <div className="text-sm font-black font-mono text-slate-300">
                            {strategy.sharpe}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full animate-pulse ${isActive ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-slate-600'}`} />
                        <span className={`text-[10px] font-black uppercase tracking-widest ${isActive ? 'text-emerald-500' : 'text-slate-500'}`}>
                            {isActive ? 'RUNNING' : 'STANDBY'}
                        </span>
                    </div>
                    <button className="text-[10px] font-black text-indigo-400 hover:text-indigo-300 uppercase tracking-widest transition-colors flex items-center gap-1">
                        Configure <Globe className="w-3 h-3" />
                    </button>
                </div>
            </div>
        </div>
    );
};

const Strategies = () => {
    const [strategies, setStrategies] = useState([
        {
            id: 'deep_swarm',
            name: 'Deep Swarm Alpha',
            type: 'AI HYBRID',
            version: '2.4.1',
            status: 'ACTIVE',
            icon: <Zap className="w-6 h-6" />,
            winRate: 78.5,
            pnl: 145020,
            trades: 42,
            sharpe: 2.8
        },
        {
            id: 'momentum_xi',
            name: 'Momentum Sniper Xi',
            type: 'MOMENTUM',
            version: '1.0.5',
            status: 'INACTIVE',
            icon: <TrendingUp className="w-6 h-6" />,
            winRate: 62.1,
            pnl: 45200,
            trades: 115,
            sharpe: 1.4
        },
        {
            id: 'mean_reversion',
            name: 'Orion Reversion',
            type: 'MEAN REV',
            version: '3.2.0',
            status: 'INACTIVE',
            icon: <Activity className="w-6 h-6" />,
            winRate: 55.4,
            pnl: -1200,
            trades: 8,
            sharpe: 0.9
        },
        {
            id: 'gamma_scalp',
            name: 'Gamma Scalper',
            type: 'OPTIONS',
            version: '0.9.beta',
            status: 'INACTIVE',
            icon: <Clock className="w-6 h-6" />,
            winRate: 48.2,
            pnl: 8500,
            trades: 230,
            sharpe: 1.1
        }
    ]);

    const toggleStrategy = (id) => {
        setStrategies(prev => prev.map(s =>
            s.id === id ? { ...s, status: s.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE' } : s
        ));
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* HUD Header */}
            <div className="flex flex-col md:flex-row gap-6">
                <HUDCard title="ACTIVE DEPLOYMENTS" neonColor="emerald" className="flex-1">
                    <div className="p-6 flex items-center gap-6">
                        <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
                            <Play className="w-8 h-8 text-emerald-500 ml-1" />
                        </div>
                        <div>
                            <div className="text-3xl font-black text-white font-mono">
                                <ScrambleText text="1" />/<span className="text-slate-500">4</span>
                            </div>
                            <div className="text-[10px] font-black uppercase text-emerald-400 tracking-[0.2em] mt-1">
                                SYSTEMS ONLINE
                            </div>
                        </div>
                    </div>
                </HUDCard>

                <HUDCard title="AGGREGATE PERFORMANCE" neonColor="indigo" className="flex-1">
                    <div className="p-6 flex items-center gap-6">
                        <div className="w-16 h-16 bg-indigo-500/10 rounded-full flex items-center justify-center border border-indigo-500/20 shadow-[0_0_20px_rgba(99,102,241,0.1)]">
                            <Award className="w-8 h-8 text-indigo-500" />
                        </div>
                        <div>
                            <div className="text-3xl font-black text-white font-mono">
                                +<ScrambleText text="198,720" />
                            </div>
                            <div className="text-[10px] font-black uppercase text-indigo-400 tracking-[0.2em] mt-1">
                                TOTAL YIELD (INR)
                            </div>
                        </div>
                    </div>
                </HUDCard>
            </div>

            {/* Strategy Grid */}
            <div>
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
                        <TrendingDown className="w-6 h-6 text-indigo-500" />
                        Command Center
                    </h3>
                    <div className="flex gap-2">
                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-white transition-all">
                            Filter
                        </button>
                        <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-[10px] font-black uppercase tracking-widest text-white shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-2">
                            <Zap className="w-3 h-3" /> Create New
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {strategies.map(strategy => (
                        <StrategyCard
                            key={strategy.id}
                            strategy={strategy}
                            onToggle={toggleStrategy}
                        />
                    ))}

                    {/* Add New Placeholder */}
                    <button className="group relative p-6 rounded-3xl border border-dashed border-white/10 hover:border-indigo-500/30 bg-black/20 hover:bg-indigo-500/5 transition-all duration-300 flex flex-col items-center justify-center gap-4 min-h-[300px]">
                        <div className="w-16 h-16 rounded-full bg-white/5 group-hover:bg-indigo-500/10 flex items-center justify-center border border-white/5 group-hover:border-indigo-500/20 transition-all">
                            <Zap className="w-6 h-6 text-slate-600 group-hover:text-indigo-400" />
                        </div>
                        <div className="text-center">
                            <div className="text-sm font-black uppercase tracking-widest text-slate-500 group-hover:text-indigo-400 transition-colors">
                                Deploy New Strategy
                            </div>
                            <div className="text-[10px] text-slate-600 mt-2 max-w-[150px] mx-auto">
                                Import python model or build via visual editor
                            </div>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Strategies;
