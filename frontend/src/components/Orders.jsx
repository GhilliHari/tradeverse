import React, { useState, useEffect, useCallback } from 'react';
import {
    ListOrdered, CheckCircle, XCircle, Clock,
    Target, AlertCircle, RefreshCw, Filter, Calendar, Cloud
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import { API_URL } from '../config/api';

const OrderRow = ({ order }) => {
    const statusMap = {
        EXECUTED: { badge: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400', icon: CheckCircle, text: 'Executed' },
        COMPLETE: { badge: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400', icon: CheckCircle, text: 'Executed' },
        FILLED: { badge: 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400', icon: CheckCircle, text: 'Filled' },
        PENDING: { badge: 'bg-amber-500/20 border-amber-500/30 text-amber-400', icon: Clock, text: 'Pending' },
        OPEN: { badge: 'bg-amber-500/20 border-amber-500/30 text-amber-400', icon: Clock, text: 'Open' },
        REJECTED: { badge: 'bg-red-500/20 border-red-500/30 text-red-400', icon: XCircle, text: 'Rejected' },
        CANCELLED: { badge: 'bg-slate-500/20 border-slate-500/30 text-slate-400', icon: XCircle, text: 'Cancelled' }
    };

    const normStatus = (order.status || 'PENDING').toUpperCase();
    const { badge, icon: StatusIcon, text } = statusMap[normStatus] || statusMap.PENDING;

    return (
        <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-white">{order.symbol}</h4>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${order.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                            {order.type}
                        </span>
                        <span className="text-[10px] font-black px-2 py-0.5 rounded uppercase bg-indigo-500/20 text-indigo-400">
                            {order.orderType}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">
                            {order.exchange || 'NFO'}
                        </span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] text-slate-500 font-mono">
                        <span>ID: {order.id}</span>
                        <span>Time: {order.timestamp}</span>
                        <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">
                            {order.source || 'ANGEL_LIVE'}
                        </span>
                    </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${badge}`}>
                    <StatusIcon className="w-3 h-3" />
                    <span className="text-xs font-bold uppercase">{text}</span>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-3 pt-3 border-t border-white/10">
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Qty</div>
                    <div className="text-sm font-mono text-white">{order.qty}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">
                        {order.orderType === 'LIMIT' ? 'Limit Price' : 'Order Price'}
                    </div>
                    <div className="text-sm font-mono text-white">
                        {order.price ? `₹${Number(order.price).toFixed(2)}` : 'MKT'}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Filled</div>
                    <div className="text-sm font-mono text-white">{order.filled}/{order.qty}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Avg Fill Price</div>
                    <div className="text-sm font-mono text-white">
                        {order.avgPrice ? `₹${Number(order.avgPrice).toFixed(2)}` : '-'}
                    </div>
                </div>
            </div>

            {order.rejectReason && (
                <div className="mt-3 pt-3 border-t border-white/10">
                    <div className="flex items-center gap-2 text-xs text-red-400">
                        <AlertCircle className="w-3 h-3" />
                        <span>{order.rejectReason}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

const Orders = () => {
    const [orders, setOrders] = useState([]);
    const [auditLog, setAuditLog] = useState([]);
    const [cloudPulse, setCloudPulse] = useState(null);
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [isLoading, setIsLoading] = useState(false);

    const fetchLiveOrders = useCallback(async () => {
        setIsLoading(true);
        try {
            const [ordRes, auditRes, pulseRes] = await Promise.all([
                fetch(`${API_URL}/api/orders`).catch(() => null),
                fetch(`${API_URL}/api/execution/audit_log`).catch(() => null),
                fetch(`${API_URL}/api/cloud/pulse`).catch(() => null)
            ]);

            if (ordRes && ordRes.ok) {
                const rawOrders = await ordRes.json();
                if (Array.isArray(rawOrders)) {
                    const normalized = rawOrders.map((o, idx) => {
                        const rawSt = String(o.status || 'PENDING').toUpperCase();
                        let mappedStatus = 'PENDING';
                        if (['COMPLETE', 'EXECUTED', 'FILLED'].includes(rawSt)) mappedStatus = 'EXECUTED';
                        else if (['REJECTED'].includes(rawSt)) mappedStatus = 'REJECTED';
                        else if (['CANCELLED', 'CANCELED'].includes(rawSt)) mappedStatus = 'CANCELLED';

                        return {
                            id: o.order_id || o.exchange_order_id || `ORD-${idx + 1}`,
                            timestamp: o.order_timestamp || new Date().toLocaleTimeString(),
                            symbol: o.tradingsymbol || 'NFO Contract',
                            exchange: o.exchange || 'NFO',
                            type: o.transaction_type || 'BUY',
                            orderType: o.order_type || (Number(o.price) > 0 ? 'LIMIT' : 'MARKET'),
                            qty: Number(o.quantity || 0),
                            price: Number(o.price || 0),
                            status: mappedStatus,
                            filled: Number(o.filled_quantity ?? o.quantity ?? 0),
                            avgPrice: Number(o.average_price || o.price || 0),
                            source: o.product === 'INTRADAY' ? 'CLOUD_AUTOPILOT' : (o.product || 'ANGEL_ONE'),
                            rejectReason: o.status_message || null
                        };
                    });
                    setOrders(normalized);
                }
            }

            if (auditRes && auditRes.ok) {
                const auditData = await auditRes.json();
                if (auditData && Array.isArray(auditData.audit_log)) {
                    setAuditLog(auditData.audit_log);
                }
            }

            if (pulseRes && pulseRes.ok) {
                const pData = await pulseRes.json();
                setCloudPulse(pData);
            }
        } catch (err) {
            console.error('Failed to fetch live orders:', err);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchLiveOrders();
        const interval = setInterval(fetchLiveOrders, 10000);
        return () => clearInterval(interval);
    }, [fetchLiveOrders]);

    const executedCount = orders.filter(o => o.status === 'EXECUTED').length;
    const pendingCount = orders.filter(o => o.status === 'PENDING').length;
    const rejectedCount = orders.filter(o => o.status === 'REJECTED').length;
    const totalVolume = orders.reduce((acc, o) => acc + (Number(o.qty) || 0), 0);
    const successRate = orders.length > 0 ? ((executedCount / orders.length) * 100).toFixed(1) : '100.0';
    const avgLatencyMs = auditLog.length > 0
        ? Math.round(auditLog.reduce((s, a) => s + (Number(a.latency_ms) || 120), 0) / auditLog.length)
        : 115;

    const filteredOrders = filterStatus === 'ALL'
        ? orders
        : orders.filter(o => o.status === filterStatus);

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* 24/7 Cloud Autonomous Banner */}
            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    <Cloud className="w-5 h-5 text-emerald-400 animate-pulse" />
                    <div>
                        <div className="text-xs font-black uppercase tracking-wider text-emerald-400">
                            24/7 Cloud Autonomous Order Engine ({cloudPulse?.env || 'LIVE'} • {cloudPulse?.active_broker || 'ANGEL ONE'})
                        </div>
                        <div className="text-[11px] text-slate-300 font-mono">
                            iMac Offline Mode: ACTIVE • Mode: {cloudPulse?.trading_mode || 'AUTO'} • Last Cloud Cycle: {cloudPulse?.autonomous_state?.last_status || 'READY'}
                        </div>
                    </div>
                </div>
                <div className="text-right font-mono text-xs text-slate-300">
                    <div>Available Cash: <span className="text-emerald-400 font-bold">₹{Number(cloudPulse?.funds?.availablecash || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span></div>
                    <div className="text-[10px] text-slate-400">IST: {cloudPulse?.ist_time || 'Synced'}</div>
                </div>
            </div>

            {/* Order Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <ListOrdered className="w-4 h-4 text-indigo-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Total Orders</span>
                    </div>
                    <div className="text-3xl font-black text-white font-mono">{orders.length}</div>
                    <div className="text-[10px] text-slate-500 mt-1">Volume: {totalVolume} Qty</div>
                </div>

                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Executed</span>
                    </div>
                    <div className="text-3xl font-black text-emerald-400 font-mono">{executedCount}</div>
                    <div className="text-[10px] text-emerald-400 mt-1">{successRate}% Fill Rate</div>
                </div>

                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-amber-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Pending</span>
                    </div>
                    <div className="text-3xl font-black text-amber-400 font-mono">{pendingCount}</div>
                    <div className="text-[10px] text-slate-500 mt-1">Awaiting Fill</div>
                </div>

                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-cyan-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Avg Latency</span>
                    </div>
                    <div className="text-3xl font-black text-cyan-400 font-mono">{avgLatencyMs}ms</div>
                    <div className="text-[10px] text-slate-500 mt-1">Smart Limit Chase</div>
                </div>
            </div>

            {/* Orders List */}
            <HUDCard title="LIVE ANGEL ONE ORDER BOOK" neonColor="indigo">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <button
                                onClick={fetchLiveOrders}
                                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2"
                            >
                                <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                                Refresh Live Book
                            </button>
                            <button
                                onClick={() => setFilterStatus(prev => prev === 'ALL' ? 'EXECUTED' : prev === 'EXECUTED' ? 'REJECTED' : 'ALL')}
                                className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2"
                            >
                                <Filter className="w-3 h-3" />
                                Filter: {filterStatus}
                            </button>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <Calendar className="w-3 h-3" />
                            <span>Real-Time Angel One SmartAPI Order Book</span>
                        </div>
                    </div>

                    {filteredOrders.length === 0 ? (
                        <div className="p-10 text-center rounded-xl bg-white/5 border border-white/5">
                            <div className="text-sm font-bold text-slate-300 mb-1">No Angel One Orders Placed Today Yet</div>
                            <div className="text-xs text-slate-500 font-mono">
                                24/7 Cloud Autonomous Sniper is active and scanning 5-minute intraday confluence during NSE market hours (09:15–15:30 IST).
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                            {filteredOrders.map((order, idx) => (
                                <OrderRow key={order.id || idx} order={order} />
                            ))}
                        </div>
                    )}
                </div>
            </HUDCard>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <HUDCard title="CLOUD AUTOPILOT CYCLES" neonColor="purple" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-purple-400 font-mono mb-2">
                                {cloudPulse?.autonomous_state?.cycles_today ?? 0}
                            </div>
                            <div className="text-xs text-slate-400">Autonomous Scans Today</div>
                        </div>
                        <div className="text-xs text-slate-400 font-mono text-right">
                            <div>Trades: {cloudPulse?.autonomous_state?.trades_today ?? executedCount}</div>
                            <div>Signal: {cloudPulse?.autonomous_state?.last_signal || 'HOLD'}</div>
                        </div>
                    </div>
                </HUDCard>

                <HUDCard title="SMART EXECUTIONS" neonColor="cyan" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-cyan-400 font-mono mb-2">{auditLog.length}</div>
                            <div className="text-xs text-slate-400">Limit-Chased Orders</div>
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                            <div>Max Cap: ₹{Number(cloudPulse?.risk?.max_position_size || 10000).toLocaleString('en-IN')}</div>
                        </div>
                    </div>
                </HUDCard>

                <HUDCard title="REJECTED / CANCELLED" neonColor="red" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-red-400 font-mono mb-2">{rejectedCount}</div>
                            <div className="text-xs text-slate-400">Rejected Orders Today</div>
                        </div>
                        <div className="text-xs text-emerald-400 font-mono">
                            {rejectedCount === 0 ? 'Zero Rejections' : 'Check Margin/RMS'}
                        </div>
                    </div>
                </HUDCard>
            </div>
        </div>
    );
};

export default Orders;
