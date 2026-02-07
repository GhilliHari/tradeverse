import React, { useState, useEffect } from 'react';
import {
    Activity, Cpu, Database, Zap, Shield, AlertTriangle,
    CheckCircle, XCircle, Clock, TrendingUp, Server, Wifi
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area, AreaChart } from 'recharts';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- SYSTEM HEALTH DATA ---

// Service Status
const services = [
    { name: 'Backend API', status: 'operational', uptime: '99.8%', latency: '45ms' },
    { name: 'Data Pipeline', status: 'operational', uptime: '99.9%', latency: '120ms' },
    { name: 'Model Engine', status: 'operational', uptime: '99.7%', latency: '230ms' },
    { name: 'Risk Engine', status: 'operational', uptime: '100%', latency: '12ms' },
    { name: 'Angel One API', status: 'operational', uptime: '98.5%', latency: '180ms' },
    { name: 'Intelligence Layer', status: 'degraded', uptime: '97.2%', latency: '450ms' }
];

// Model Performance Metrics
const modelMetrics = [
    { metric: 'Daily Model Accuracy', value: '82.4%', status: 'excellent', target: '80%' },
    { metric: 'Intraday Model Accuracy', value: '76.8%', status: 'good', target: '75%' },
    { metric: 'Precision (Sniper)', value: '84.2%', status: 'excellent', target: '80%' },
    { metric: 'False Positive Rate', value: '8.5%', status: 'good', target: '<10%' },
    { metric: 'Signal Latency', value: '1.2s', status: 'excellent', target: '<2s' },
    { metric: 'OOD Detection Rate', value: '94.1%', status: 'excellent', target: '>90%' }
];

// API Latency History (last 24 hours)
const latencyData = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    api: 40 + Math.random() * 30,
    model: 200 + Math.random() * 100,
    data: 100 + Math.random() * 50
}));

// System Resources
const systemResources = {
    cpu: 34,
    memory: 62,
    disk: 45,
    network: 28
};

// Recent Events Log
const eventLog = [
    { time: '14:32', type: 'INFO', message: 'Model artifacts loaded successfully (Daily + Intraday)' },
    { time: '14:15', type: 'WARNING', message: 'Intelligence Layer: Gemini API rate limit approaching (85%)' },
    { time: '13:45', type: 'SUCCESS', message: 'Data Pipeline: Fetched 2,847 candles for BANKNIFTY' },
    { time: '12:20', type: 'INFO', message: 'Risk Engine: Circuit breaker test passed' },
    { time: '11:05', type: 'ERROR', message: 'Angel One: LTP fetch timeout (retry successful)' },
    { time: '10:30', type: 'SUCCESS', message: 'Training completed: F1 Score improved to 0.78' }
];

const StatusBadge = ({ status }) => {
    const config = {
        operational: { color: 'emerald', icon: CheckCircle, text: 'Operational' },
        degraded: { color: 'amber', icon: AlertTriangle, text: 'Degraded' },
        down: { color: 'red', icon: XCircle, text: 'Down' }
    };

    const { color, icon: Icon, text } = config[status] || config.operational;

    return (
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full bg-${color}-500/20 border border-${color}-500/30`}>
            <Icon className={`w-3 h-3 text-${color}-400`} />
            <span className={`text-xs font-bold text-${color}-400 uppercase tracking-wider`}>{text}</span>
        </div>
    );
};

const ServiceRow = ({ service }) => (
    <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
        <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${service.status === 'operational' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse' :
                        service.status === 'degraded' ? 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]' :
                            'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]'
                    }`} />
                <h4 className="font-bold text-white">{service.name}</h4>
            </div>
            <StatusBadge status={service.status} />
        </div>
        <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
                <span className="text-slate-500">Uptime:</span>
                <span className="ml-2 font-mono font-bold text-emerald-400">{service.uptime}</span>
            </div>
            <div>
                <span className="text-slate-500">Latency:</span>
                <span className="ml-2 font-mono font-bold text-cyan-400">{service.latency}</span>
            </div>
        </div>
    </div>
);

const MetricRow = ({ metric }) => (
    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
        <div className="flex-1">
            <div className="text-sm text-slate-300 font-medium">{metric.metric}</div>
            <div className="text-[10px] text-slate-500 mt-1">Target: {metric.target}</div>
        </div>
        <div className="text-right">
            <div className={`text-lg font-mono font-bold ${metric.status === 'excellent' ? 'text-emerald-400' :
                    metric.status === 'good' ? 'text-cyan-400' : 'text-amber-400'
                }`}>
                {metric.value}
            </div>
        </div>
    </div>
);

const ResourceGauge = ({ label, value, icon: Icon }) => (
    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
        <div className="flex items-center gap-2 mb-3">
            <Icon className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
        </div>
        <div className="relative">
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                <div
                    className={`h-full transition-all duration-500 ${value > 80 ? 'bg-red-500' :
                            value > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`}
                    style={{ width: `${value}%` }}
                />
            </div>
            <div className="text-right mt-2">
                <span className="text-xl font-mono font-bold text-white">{value}%</span>
            </div>
        </div>
    </div>
);

const SystemHealth = () => {
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">

            {/* Header Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Services Up</span>
                    </div>
                    <div className="text-3xl font-black text-emerald-400 font-mono">5/6</div>
                    <div className="text-[10px] text-slate-500 mt-1">83% Operational</div>
                </div>

                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-cyan-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Avg Latency</span>
                    </div>
                    <div className="text-3xl font-black text-cyan-400 font-mono">45ms</div>
                    <div className="text-[10px] text-slate-500 mt-1">API Response</div>
                </div>

                <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-purple-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Model Accuracy</span>
                    </div>
                    <div className="text-3xl font-black text-purple-400 font-mono">82.4%</div>
                    <div className="text-[10px] text-slate-500 mt-1">Daily Strategist</div>
                </div>

                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Shield className="w-4 h-4 text-indigo-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Risk Engine</span>
                    </div>
                    <div className="text-3xl font-black text-indigo-400 font-mono">100%</div>
                    <div className="text-[10px] text-slate-500 mt-1">Uptime</div>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Services Status */}
                <div className="lg:col-span-2 space-y-6">
                    <HUDCard title="SERVICE STATUS" neonColor="emerald">
                        <div className="p-6 space-y-3">
                            {services.map((service, idx) => (
                                <ServiceRow key={idx} service={service} />
                            ))}
                        </div>
                    </HUDCard>

                    {/* Latency Chart */}
                    <HUDCard title="API LATENCY (24H)" neonColor="cyan" className="h-[300px]">
                        <div className="p-6 h-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={latencyData}>
                                    <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#000000ee', border: '1px solid #333', borderRadius: '8px' }}
                                        formatter={(value) => [`${value.toFixed(0)}ms`, '']}
                                    />
                                    <Line type="monotone" dataKey="api" stroke="#06b6d4" strokeWidth={2} dot={false} name="API" />
                                    <Line type="monotone" dataKey="model" stroke="#a855f7" strokeWidth={2} dot={false} name="Model" />
                                    <Line type="monotone" dataKey="data" stroke="#10b981" strokeWidth={2} dot={false} name="Data" />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </HUDCard>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* System Resources */}
                    <HUDCard title="SYSTEM RESOURCES" neonColor="indigo">
                        <div className="p-6 space-y-4">
                            <ResourceGauge label="CPU" value={systemResources.cpu} icon={Cpu} />
                            <ResourceGauge label="Memory" value={systemResources.memory} icon={Database} />
                            <ResourceGauge label="Disk" value={systemResources.disk} icon={Server} />
                            <ResourceGauge label="Network" value={systemResources.network} icon={Wifi} />
                        </div>
                    </HUDCard>
                </div>
            </div>

            {/* Model Performance */}
            <HUDCard title="MODEL PERFORMANCE METRICS" neonColor="purple">
                <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {modelMetrics.map((metric, idx) => (
                        <MetricRow key={idx} metric={metric} />
                    ))}
                </div>
            </HUDCard>

            {/* Event Log */}
            <HUDCard title="SYSTEM EVENT LOG" neonColor="amber">
                <div className="p-6 space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {eventLog.map((event, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all font-mono text-xs">
                            <span className="text-slate-500 flex-shrink-0">{event.time}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase flex-shrink-0 ${event.type === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-400' :
                                    event.type === 'ERROR' ? 'bg-red-500/20 text-red-400' :
                                        event.type === 'WARNING' ? 'bg-amber-500/20 text-amber-400' :
                                            'bg-cyan-500/20 text-cyan-400'
                                }`}>
                                {event.type}
                            </span>
                            <span className="text-slate-300 flex-1">{event.message}</span>
                        </div>
                    ))}
                </div>
            </HUDCard>
        </div>
    );
};

export default SystemHealth;
