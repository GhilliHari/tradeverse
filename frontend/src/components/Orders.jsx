import React from 'react';
import {
    ListOrdered, CheckCircle, XCircle, Clock, TrendingUp, TrendingDown,
    DollarSign, Target, AlertCircle, RefreshCw, Filter, Calendar
} from 'lucide-react';
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';

// --- ORDERS DATA ---

// Order History (Recent + Active)
const orders = [
    {
        id: 'ORD-2024-001',
        timestamp: '14:32:15',
        symbol: 'BankNifty 48200 CE',
        type: 'BUY',
        orderType: 'LIMIT',
        qty: 50,
        price: 245.00,
        status: 'EXECUTED',
        filled: 50,
        avgPrice: 244.50,
        pnl: null,
        source: 'AI_SNIPER'
    },
    {
        id: 'ORD-2024-002',
        timestamp: '13:15:42',
        symbol: 'HDFC Bank',
        type: 'BUY',
        orderType: 'MARKET',
        qty: 50,
        price: null,
        status: 'EXECUTED',
        filled: 50,
        avgPrice: 1580.20,
        pnl: null,
        source: 'MANUAL'
    },
    {
        id: 'ORD-2024-003',
        timestamp: '12:45:30',
        symbol: 'BankNifty 47800 PE',
        type: 'BUY',
        orderType: 'LIMIT',
        qty: 50,
        price: 180.00,
        status: 'EXECUTED',
        filled: 50,
        avgPrice: 180.00,
        pnl: null,
        source: 'AI_STRATEGIST'
    },
    {
        id: 'ORD-2024-004',
        timestamp: '11:20:18',
        symbol: 'BankNifty 48500 CE',
        type: 'SELL',
        orderType: 'LIMIT',
        qty: 50,
        price: 150.00,
        status: 'EXECUTED',
        filled: 50,
        avgPrice: 152.50,
        pnl: 3750,
        source: 'AI_SNIPER'
    },
    {
        id: 'ORD-2024-005',
        timestamp: '10:15:05',
        symbol: 'ICICI Bank',
        type: 'BUY',
        orderType: 'MARKET',
        qty: 30,
        price: null,
        status: 'EXECUTED',
        filled: 30,
        avgPrice: 1065.00,
        pnl: null,
        source: 'MANUAL'
    },
    {
        id: 'ORD-2024-006',
        timestamp: '09:30:22',
        symbol: 'BankNifty 48000 PE',
        type: 'BUY',
        orderType: 'LIMIT',
        qty: 50,
        price: 200.00,
        status: 'PENDING',
        filled: 0,
        avgPrice: null,
        pnl: null,
        source: 'AI_STRATEGIST'
    },
    {
        id: 'ORD-2024-007',
        timestamp: '09:18:45',
        symbol: 'BankNifty 47500 CE',
        type: 'SELL',
        orderType: 'LIMIT',
        qty: 50,
        price: 280.00,
        status: 'REJECTED',
        filled: 0,
        avgPrice: null,
        pnl: null,
        source: 'AI_SNIPER',
        rejectReason: 'Insufficient margin'
    }
];

// Order Statistics
const orderStats = {
    totalOrders: 7,
    executed: 5,
    pending: 1,
    rejected: 1,
    totalVolume: 330,
    avgExecutionTime: '1.2s',
    successRate: 85.7
};

const OrderRow = ({ order }) => {
    const statusConfig = {
        EXECUTED: { color: 'emerald', icon: CheckCircle, text: 'Executed' },
        PENDING: { color: 'amber', icon: Clock, text: 'Pending' },
        REJECTED: { color: 'red', icon: XCircle, text: 'Rejected' },
        CANCELLED: { color: 'slate', icon: XCircle, text: 'Cancelled' }
    };

    const { color, icon: StatusIcon, text } = statusConfig[order.status] || statusConfig.PENDING;

    return (
        <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
            <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-white">{order.symbol}</h4>
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${order.type === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                            }`}>
                            {order.type}
                        </span>
                        <span className="text-[10px] font-black px-2 py-0.5 rounded uppercase bg-indigo-500/20 text-indigo-400">
                            {order.orderType}
                        </span>
                    </div>
                    <div className="flex items-center gap-4 text-[10px] text-slate-500 font-mono">
                        <span>ID: {order.id}</span>
                        <span>Time: {order.timestamp}</span>
                        <span className={`px-2 py-0.5 rounded ${order.source === 'AI_SNIPER' ? 'bg-purple-500/20 text-purple-400' :
                                order.source === 'AI_STRATEGIST' ? 'bg-cyan-500/20 text-cyan-400' :
                                    'bg-slate-500/20 text-slate-400'
                            }`}>
                            {order.source}
                        </span>
                    </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full bg-${color}-500/20 border border-${color}-500/30`}>
                    <StatusIcon className={`w-3 h-3 text-${color}-400`} />
                    <span className={`text-xs font-bold text-${color}-400 uppercase`}>{text}</span>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-3 pt-3 border-t border-white/10">
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Qty</div>
                    <div className="text-sm font-mono text-white">{order.qty}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">
                        {order.orderType === 'LIMIT' ? 'Limit Price' : 'Market'}
                    </div>
                    <div className="text-sm font-mono text-white">
                        {order.price ? `₹${order.price.toFixed(2)}` : 'MKT'}
                    </div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Filled</div>
                    <div className="text-sm font-mono text-white">{order.filled}/{order.qty}</div>
                </div>
                <div>
                    <div className="text-[10px] text-slate-500 font-bold uppercase mb-1">Avg Price</div>
                    <div className="text-sm font-mono text-white">
                        {order.avgPrice ? `₹${order.avgPrice.toFixed(2)}` : '-'}
                    </div>
                </div>
            </div>

            {order.pnl !== null && (
                <div className="mt-3 pt-3 border-t border-white/10">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Realized P&L</span>
                        <span className={`text-sm font-mono font-bold ${order.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {order.pnl >= 0 ? '+' : ''}₹{order.pnl.toLocaleString()}
                        </span>
                    </div>
                </div>
            )}

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
    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">

            {/* Order Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <ListOrdered className="w-4 h-4 text-indigo-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Total Orders</span>
                    </div>
                    <div className="text-3xl font-black text-white font-mono">{orderStats.totalOrders}</div>
                    <div className="text-[10px] text-slate-500 mt-1">Volume: {orderStats.totalVolume}</div>
                </div>

                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Executed</span>
                    </div>
                    <div className="text-3xl font-black text-emerald-400 font-mono">{orderStats.executed}</div>
                    <div className="text-[10px] text-emerald-400 mt-1">{orderStats.successRate}% Success</div>
                </div>

                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-amber-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Pending</span>
                    </div>
                    <div className="text-3xl font-black text-amber-400 font-mono">{orderStats.pending}</div>
                    <div className="text-[10px] text-slate-500 mt-1">Awaiting Fill</div>
                </div>

                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-cyan-400" />
                        <span className="text-[10px] uppercase font-black text-slate-500 tracking-wider">Avg Speed</span>
                    </div>
                    <div className="text-3xl font-black text-cyan-400 font-mono">{orderStats.avgExecutionTime}</div>
                    <div className="text-[10px] text-slate-500 mt-1">Execution Time</div>
                </div>
            </div>

            {/* Orders List */}
            <HUDCard title="ORDER BOOK" neonColor="indigo">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <button className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2">
                                <RefreshCw className="w-3 h-3" />
                                Refresh
                            </button>
                            <button className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-2">
                                <Filter className="w-3 h-3" />
                                Filter
                            </button>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <Calendar className="w-3 h-3" />
                            <span>Today's Orders</span>
                        </div>
                    </div>

                    <div className="space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                        {orders.map((order, idx) => (
                            <OrderRow key={idx} order={order} />
                        ))}
                    </div>
                </div>
            </HUDCard>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <HUDCard title="AI ORDERS" neonColor="purple" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-purple-400 font-mono mb-2">4</div>
                            <div className="text-xs text-slate-400">AI-Generated Trades</div>
                        </div>
                        <div className="text-xs text-slate-500">
                            <div>Sniper: 2</div>
                            <div>Strategist: 2</div>
                        </div>
                    </div>
                </HUDCard>

                <HUDCard title="MANUAL ORDERS" neonColor="cyan" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-cyan-400 font-mono mb-2">2</div>
                            <div className="text-xs text-slate-400">User-Initiated Trades</div>
                        </div>
                        <div className="text-xs text-slate-500">
                            <div>Equity: 2</div>
                        </div>
                    </div>
                </HUDCard>

                <HUDCard title="REJECTED" neonColor="red" className="h-[150px]">
                    <div className="p-6 flex items-center justify-between h-full">
                        <div>
                            <div className="text-4xl font-black text-red-400 font-mono mb-2">1</div>
                            <div className="text-xs text-slate-400">Failed Orders</div>
                        </div>
                        <div className="text-xs text-red-400">
                            Margin Issue
                        </div>
                    </div>
                </HUDCard>
            </div>
        </div>
    );
};

export default Orders;
