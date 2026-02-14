import React, { useState, useEffect } from 'react';
import {
    Telescope, Search, Download, FileText,
    Filter, ChevronDown, Rocket, Eye
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || "";

const Observatory = ({ token }) => {
    const [logs, setLogs] = useState([]);
    const [filter, setFilter] = useState('ALL'); // ALL, OPEN, CLOSE
    const [searchTerm, setSearchTerm] = useState('');

    const fetchHistory = async () => {
        try {
            const res = await fetch(`${API_URL}/api/paper/history`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            // Sort by timestamp desc
            setLogs(data.reverse());
        } catch (e) {
            console.error("Failed to fetch history", e);
        }
    };

    useEffect(() => {
        if (token) fetchHistory();
    }, [token]);

    const filteredLogs = logs.filter(log => {
        if (filter !== 'ALL' && log.action !== filter) return false;
        if (searchTerm && !JSON.stringify(log).toLowerCase().includes(searchTerm.toLowerCase())) return false;
        return true;
    });

    const exportData = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(logs, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", `trade_observatory_${new Date().toISOString()}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header / Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/50 backdrop-blur-sm p-6 rounded-2xl border border-indigo-500/20 shadow-xl">
                <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400">
                        <Telescope className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Pattern Observatory</h2>
                        <p className="text-sm text-slate-400">Review simulated trades & detect edge evolution.</p>
                    </div>
                </div>

                <div className="flex gap-3 w-full md:w-auto">
                    <div className="relative flex-1 md:w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                        />
                    </div>
                    <button
                        onClick={exportData}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold text-white transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        EXPORT
                    </button>
                </div>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                    { label: 'Total Logs', value: logs.length, color: 'text-white' },
                    { label: 'Open Trades', value: logs.filter(l => l.action === 'OPEN' && l.status === 'OPEN').length, color: 'text-indigo-400' },
                    { label: 'Realized PnL', value: logs.filter(l => l.action === 'CLOSE').reduce((acc, curr) => acc + (curr.pnl || 0), 0).toFixed(2), color: 'text-emerald-400' },
                    {
                        label: 'Win Rate', value: (() => {
                            const closed = logs.filter(l => l.action === 'CLOSE');
                            if (closed.length === 0) return '0%';
                            const wins = closed.filter(l => l.pnl > 0).length;
                            return `${((wins / closed.length) * 100).toFixed(1)}%`;
                        })(), color: 'text-purple-400'
                    }
                ].map((stat, i) => (
                    <div key={i} className="bg-slate-900/40 p-4 rounded-xl border border-white/5">
                        <p className="text-xs text-slate-500 uppercase font-bold">{stat.label}</p>
                        <p className={`text-xl font-mono font-bold mt-1 ${stat.color}`}>{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* Data Table */}
            <div className="bg-slate-900/50 backdrop-blur-sm rounded-2xl border border-indigo-500/10 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-indigo-500/20 bg-indigo-500/5 text-xs uppercase text-slate-400">
                                <th className="p-4 font-bold">Time</th>
                                <th className="p-4 font-bold">Action</th>
                                <th className="p-4 font-bold">Symbol</th>
                                <th className="p-4 font-bold">Side</th>
                                <th className="p-4 font-bold">Price</th>
                                <th className="p-4 font-bold">PnL</th>
                                <th className="p-4 font-bold">Mode</th>
                                <th className="p-4 font-bold">Logic / Notes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                            {filteredLogs.map((log, idx) => (
                                <tr key={idx} className="hover:bg-white/5 transition-colors text-sm">
                                    <td className="p-4 font-mono text-slate-400 whitespace-nowrap">
                                        {new Date(log.timestamp).toLocaleDateString()} <br />
                                        <span className="text-xs opacity-60">{new Date(log.timestamp).toLocaleTimeString()}</span>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase ${log.action === 'OPEN' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-600/20 text-slate-400'
                                            }`}>
                                            {log.action}
                                        </span>
                                    </td>
                                    <td className="p-4 font-bold text-white">{log.symbol}</td>
                                    <td className="p-4">
                                        <span className={`font-bold ${log.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {log.side}
                                        </span>
                                    </td>
                                    <td className="p-4 font-mono text-slate-300">
                                        {log.action === 'OPEN' ? log.entry_price : log.exit_price}
                                    </td>
                                    <td className="p-4 font-mono font-bold">
                                        {log.pnl !== undefined ? (
                                            <span className={log.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                                                {log.pnl > 0 ? '+' : ''}{log.pnl}
                                            </span>
                                        ) : '-'}
                                    </td>
                                    <td className="p-4 text-xs text-slate-500">{log.mode}</td>
                                    <td className="p-4 max-w-xs truncate text-slate-400 italic">
                                        "{log.reasoning}"
                                    </td>
                                </tr>
                            ))}
                            {filteredLogs.length === 0 && (
                                <tr>
                                    <td colSpan="8" className="p-8 text-center text-slate-500">
                                        No logs found matching your criteria.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Observatory;
