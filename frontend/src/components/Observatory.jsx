import React, { useState, useEffect } from 'react';
import {
    Activity, Play, StopCircle, Target, TrendingUp, TrendingDown,
    DollarSign, Percent, Clock, BarChart3, CheckCircle, XCircle,
    AlertCircle, Zap, Calendar, RefreshCw
} from 'lucide-react';

const getApiUrl = () => {
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved) {
            if ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && saved.includes('trycloudflare.com')) {
                localStorage.removeItem('tradeverse_api_url');
            } else {
                return saved.replace(/\/$/, '');
            }
        }
    } catch (e) { }
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};
const API_URL = getApiUrl();
const GITHUB_RAW_SUMMARY_URL = 'https://raw.githubusercontent.com/GhilliHari/tradeverse/main/backend/observatory_data/latest_summary.json';

const Observatory = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [isMarketHours, setIsMarketHours] = useState(false);
    const [activePredictions, setActivePredictions] = useState(0);
    const [completedToday, setCompletedToday] = useState(0);
    const [githubBackupInfo, setGithubBackupInfo] = useState({
        repo: 'GhilliHari/tradeverse',
        commit: 'main',
        mode: 'GitHub Backed'
    });

    const [summary, setSummary] = useState({
        total_predictions: 0,
        completed: 0,
        pending: 0,
        win_rate: 0,
        avg_pnl: 0,
        total_pnl: 0,
        profitable_count: 0,
        loss_count: 0
    });

    const [recentPredictions, setRecentPredictions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);

    const token = localStorage.getItem('token');

    const loadFromGitHubFallback = async () => {
        try {
            const res = await fetch(`${GITHUB_RAW_SUMMARY_URL}?t=${Date.now()}`);
            if (res.ok) {
                const data = await res.json();
                if (data.status) {
                    setIsRunning(Boolean(data.status.is_running));
                    setIsMarketHours(Boolean(data.status.is_market_hours));
                    setActivePredictions(data.status.active_predictions || 0);
                    setCompletedToday(data.status.completed_today || 0);
                }
                if (data.observatory_summary) {
                    setSummary(data.observatory_summary);
                }
                if (Array.isArray(data.recent_predictions)) {
                    setRecentPredictions(data.recent_predictions.slice(0, 20));
                }
                setGithubBackupInfo({
                    repo: data.repo || 'GhilliHari/tradeverse',
                    commit: 'Cloud Raw',
                    mode: 'GitHub Cloud Fallback'
                });
            }
        } catch (err) {
            console.error('GitHub fallback load error', err);
        }
    };

    const handleSyncMarketHours = async () => {
        setIsSyncing(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/backfill?days=14&push_github=true`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (res.ok) {
                await Promise.all([fetchStatus(), fetchSummary(), fetchRecent()]);
            } else {
                await loadFromGitHubFallback();
            }
        } catch (e) {
            await loadFromGitHubFallback();
        } finally {
            setIsSyncing(false);
        }
    };

    const fetchStatus = async () => {
        try {
            const [res, ghRes] = await Promise.all([
                fetch(`${API_URL}/api/observatory/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                }),
                fetch(`${API_URL}/api/github/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                }).catch(() => null)
            ]);
            if (!res.ok) {
                await loadFromGitHubFallback();
                return;
            }
            const data = await res.json();

            setIsRunning(data.is_running);
            setIsMarketHours(data.is_market_hours);
            setActivePredictions(data.active_predictions);
            setCompletedToday(data.completed_today);

            if (ghRes && ghRes.ok) {
                const ghData = await ghRes.json();
                setGithubBackupInfo({
                    repo: ghData.repo || 'GhilliHari/tradeverse',
                    commit: ghData.latest_commit || 'main',
                    mode: ghData.is_synced ? 'GitHub Synced' : 'GitHub Active'
                });
            }
        } catch (e) {
            await loadFromGitHubFallback();
        }
    };

    const fetchSummary = async () => {
        try {
            const res = await fetch(`${API_URL}/api/observatory/summary`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSummary(data);
            }
        } catch (e) {
            // Handled by loadFromGitHubFallback in fetchStatus
        }
    };

    const fetchRecent = async () => {
        try {
            const res = await fetch(`${API_URL}/api/observatory/results`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                const predictions = data.predictions || [];
                const sorted = predictions.sort((a, b) =>
                    new Date(b.timestamp) - new Date(a.timestamp)
                ).slice(0, 20);
                setRecentPredictions(sorted);
            }
        } catch (e) {
            // Handled by loadFromGitHubFallback in fetchStatus
        }
    };

    const handleStart = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/start`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.ok) {
                await fetchStatus();
            } else {
                const error = await res.json();
                alert(error.detail || 'Failed to start simulation');
            }
        } catch (e) {
            console.error('Failed to start observatory', e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStop = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/observatory/stop`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.ok) {
                await fetchStatus();
            } else {
                const error = await res.json();
                alert(error.detail || 'Failed to stop simulation');
            }
        } catch (e) {
            console.error('Failed to stop observatory', e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        fetchSummary();
        fetchRecent();

        // Poll every 5 seconds
        const interval = setInterval(() => {
            fetchStatus();
            fetchSummary();
            fetchRecent();
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    const getPredictionColor = (pred) => {
        if (pred.status !== 'COMPLETED' || !pred.actual_outcome) {
            return 'border-slate-700 bg-slate-900/20';
        }

        const pnl = pred.actual_outcome.pnl;
        if (pnl > 0) return 'border-emerald-500/30 bg-emerald-950/20';
        if (pnl < 0) return 'border-red-500/30 bg-red-950/20';
        return 'border-slate-700 bg-slate-900/20';
    };

    const winRate = summary.win_rate || 0;

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-4xl font-black text-white tracking-tighter flex items-center gap-4">
                        <Activity className="w-10 h-10 text-purple-500" />
                        OBSERVATORY TOOLS
                    </h2>
                    <p className="text-slate-500 font-bold uppercase tracking-[0.3em] text-[10px] ml-1 mt-2">
                        Live AI Performance Tracker
                    </p>
                </div>

                {/* Control Buttons */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleSyncMarketHours}
                        disabled={isSyncing}
                        className="px-5 py-4 rounded-2xl font-black text-xs uppercase tracking-[0.15em] transition-all shadow-lg flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/30"
                        title={`Sync market hours & backup to GitHub (${githubBackupInfo.repo} #${githubBackupInfo.commit})`}
                    >
                        <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                        {isSyncing ? 'Syncing GitHub...' : `Sync & Backup GitHub (#${githubBackupInfo.commit})`}
                    </button>

                    <button
                        onClick={isRunning ? handleStop : handleStart}
                        disabled={isLoading}
                        className={`px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all shadow-lg flex items-center gap-3 ${isRunning
                            ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-500/40'
                            : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/40'
                            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {isRunning ? (
                            <>
                                <StopCircle className="w-5 h-5" />
                                Stop Simulation
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5" />
                                Start Simulation
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Status Bar */}
            <div className="glass-panel p-6 rounded-3xl border border-purple-500/10">
                <div className="grid grid-cols-5 gap-6">
                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Status</p>
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-emerald-400 animate-pulse' : 'bg-emerald-500'}`} />
                            <p className="font-black text-sm tracking-tight text-emerald-400">
                                {isRunning ? 'LIVE ACTIVE' : '24/7 CATCH-UP READY'}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Market (9:15–15:30)</p>
                        <div className="flex items-center gap-2">
                            <Clock className={`w-4 h-4 ${isMarketHours ? 'text-emerald-400' : 'text-amber-400'}`} />
                            <p className={`font-black text-sm tracking-tight ${isMarketHours ? 'text-emerald-400' : 'text-amber-400'}`}>
                                {isMarketHours ? 'OPEN (LIVE)' : 'OFF-HOURS (SYNCED)'}
                            </p>
                        </div>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Session Date</p>
                        <p className="font-black text-lg text-white font-mono tracking-tight">{summary.date || 'Latest'}</p>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Active</p>
                        <p className="font-black text-2xl text-purple-400 tracking-tight">{activePredictions}</p>
                    </div>

                    <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Completed Session</p>
                        <p className="font-black text-2xl text-cyan-400 tracking-tight">{completedToday || summary.completed || 0}</p>
                    </div>
                </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Win Rate */}
                <div className="glass-panel p-6 rounded-3xl border border-emerald-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <Target className="w-5 h-5 text-emerald-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Win Rate</p>
                        </div>
                        <p className="text-4xl font-black text-emerald-400 tracking-tight">{winRate.toFixed(1)}%</p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">{summary.profitable_count}W / {summary.loss_count}L</p>
                    </div>
                </div>

                {/* Total P&L */}
                <div className="glass-panel p-6 rounded-3xl border border-purple-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <DollarSign className="w-5 h-5 text-purple-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Total P&L</p>
                        </div>
                        <p className={`text-4xl font-black tracking-tight ${summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            ₹{summary.total_pnl.toLocaleString('en-IN')}
                        </p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">{summary.completed} trades</p>
                    </div>
                </div>

                {/* Avg P&L */}
                <div className="glass-panel p-6 rounded-3xl border border-cyan-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <BarChart3 className="w-5 h-5 text-cyan-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Avg P&L</p>
                        </div>
                        <p className={`text-4xl font-black tracking-tight ${summary.avg_pnl >= 0 ? 'text-cyan-400' : 'text-red-400'}`}>
                            ₹{summary.avg_pnl.toLocaleString('en-IN')}
                        </p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">per trade</p>
                    </div>
                </div>

                {/* Total Predictions */}
                <div className="glass-panel p-6 rounded-3xl border border-indigo-500/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 blur-[40px] rounded-full -mr-12 -mt-12" />
                    <div className="relative">
                        <div className="flex items-center gap-2 mb-3">
                            <Zap className="w-5 h-5 text-indigo-400" />
                            <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Total Predictions</p>
                        </div>
                        <p className="text-4xl font-black text-indigo-400 tracking-tight">{summary.total_predictions}</p>
                        <p className="text-xs text-slate-500 mt-1 font-mono">{summary.pending} pending</p>
                    </div>
                </div>
            </div>

            {/* Recent Predictions Table */}
            <div className="glass-panel p-8 rounded-3xl border border-white/5">
                <h3 className="text-xl font-black text-white mb-6 flex items-center gap-3">
                    <Calendar className="w-6 h-6 text-purple-400" />
                    Recent Predictions
                </h3>

                <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar pr-4">
                    {recentPredictions.length === 0 ? (
                        <div className="text-center py-12">
                            <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-500 text-sm font-bold uppercase tracking-widest">No predictions yet</p>
                            <p className="text-slate-600 text-xs mt-1">Start the simulation to see live predictions</p>
                        </div>
                    ) : (
                        recentPredictions.map((pred, idx) => (
                            <div
                                key={idx}
                                className={`border rounded-2xl p-5 transition-all hover:border-white/20 ${getPredictionColor(pred)}`}
                            >
                                <div className="grid grid-cols-6 gap-4 items-center">
                                    {/* Time */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Time</p>
                                        <p className="text-xs font-mono text-slate-300">
                                            {new Date(pred.timestamp).toLocaleTimeString('en-IN', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>
                                    </div>

                                    {/* Signal */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Signal</p>
                                        <div className={`px-2 py-1 rounded-lg text-[10px] font-black tracking-widest inline-block ${pred.prediction.signal === 'BUY_CE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                            pred.prediction.signal === 'BUY_PE' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                                'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                                            }`}>
                                            {pred.prediction.signal}
                                        </div>
                                    </div>

                                    {/* Strike */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Strike</p>
                                        <p className="text-sm font-mono text-white font-black">{pred.prediction.strike}</p>
                                    </div>

                                    {/* Entry/Exit */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">Entry → Exit</p>
                                        <p className="text-xs font-mono text-slate-300">
                                            ₹{pred.prediction.entry_price.toFixed(2)}
                                            {pred.actual_outcome && ` → ₹${pred.actual_outcome.exit_price.toFixed(2)}`}
                                        </p>
                                    </div>

                                    {/* P&L */}
                                    <div>
                                        <p className="text-[8px] font-black uppercase text-slate-500 mb-1">P&L</p>
                                        {pred.actual_outcome ? (
                                            <div className="flex items-center gap-2">
                                                <p className={`text-sm font-black font-mono ${pred.actual_outcome.pnl > 0 ? 'text-emerald-400' :
                                                    pred.actual_outcome.pnl < 0 ? 'text-red-400' : 'text-slate-400'
                                                    }`}>
                                                    {pred.actual_outcome.pnl > 0 ? '+' : ''}₹{pred.actual_outcome.pnl.toFixed(0)}
                                                </p>
                                                <span className={`text-[10px] font-bold ${pred.actual_outcome.pnl_pct > 0 ? 'text-emerald-400' : 'text-red-400'
                                                    }`}>
                                                    ({pred.actual_outcome.pnl_pct > 0 ? '+' : ''}{pred.actual_outcome.pnl_pct.toFixed(1)}%)
                                                </span>
                                            </div>
                                        ) : (
                                            <p className="text-xs text-slate-500 font-bold">Pending...</p>
                                        )}
                                    </div>

                                    {/* Status */}
                                    <div className="text-right">
                                        {pred.status === 'COMPLETED' && pred.actual_outcome && (
                                            pred.actual_outcome.pnl > 0 ? (
                                                <CheckCircle className="w-5 h-5 text-emerald-400 ml-auto" />
                                            ) : pred.actual_outcome.pnl < 0 ? (
                                                <XCircle className="w-5 h-5 text-red-400 ml-auto" />
                                            ) : (
                                                <div className="w-5 h-5 rounded-full bg-slate-600 ml-auto" />
                                            )
                                        )}
                                        {pred.status === 'PENDING' && (
                                            <div className="w-5 h-5 rounded-full bg-amber-400/50 animate-pulse ml-auto" />
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Observatory;
