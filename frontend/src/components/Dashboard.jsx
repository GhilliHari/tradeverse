import React, { useState, useEffect, useRef, useCallback } from 'react';
// Tradeverse Dashboard Controller - v1.0.4 (Trigger Redeploy)
import {
    TrendingUp, TrendingDown, Shield, Brain, Activity,
    Settings, Zap, AlertTriangle, RefreshCw, CheckCircle, ChevronRight,
    LayoutDashboard, ListOrdered, GraduationCap, BarChart3, Database,
    Lightbulb, Briefcase, HeartPulse, User, LogOut, Terminal,
    Key, Eye, Cpu, Globe, Wifi, Bell, Search, Lock, Unlock,
    MessageCircle, Send, Menu, X
} from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, LineChart, Line
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { workerSetInterval, workerClearInterval } from '../utils/workerTimer';
import HUDCard from './ui/HUDCard';
import BrainVisualizer from './BrainVisualizer';
import ConfidenceGauge from './ConfidenceGauge';
import ScrambleText from './ui/ScrambleText';
import StatusBadge from './StatusBadge';
import LoginModal from './LoginModal';
import Backtest from './Backtest';

import Insights from './Insights';
import Smallcases from './Smallcases';
import MarketPulse from './MarketPulse';
import Portfolio from './Portfolio';
import SystemHealth from './SystemHealth';
import Orders from './Orders';
import MarketMoodIndex from './MarketMoodIndex';
import Strategies from './Strategies';
import Analytics from './Analytics';
import PaperTrade from './PaperTrade';
import Observatory from './Observatory';
import OptionChainGEX from './OptionChainGEX';
import TradeChecklist from './TradeChecklist';
import GreeksCheatSheet from './GreeksCheatSheet';
import LessonsLearned from './LessonsLearned';
import { Telescope, ScrollText, BookOpen, Layers, ShieldCheck, Clock } from 'lucide-react';
import MarketClock from './MarketClock';
import { auth } from '../firebase';


// BASE API URL
const getApiUrl = () => {
    try {
        const saved = localStorage.getItem('tradeverse_api_url');
        if (saved) {
            if ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:') && saved.includes('trycloudflare.com')) {
                localStorage.removeItem('tradeverse_api_url');
            } else {
                return saved.replace(/\/$/, '');
            }
        }
    } catch (e) { }
    if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
        return 'http://localhost:8000';
    }
    return ""; // Default to relative (Vite/Vercel proxy)
};
const API_URL = getApiUrl();

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-1.5 px-1.5 py-1 rounded-lg transition-all duration-300 group ${active
            ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/5'
            : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border border-transparent'
            }`}
    >
        <Icon className={`w-3.5 h-3.5 ${active ? 'text-indigo-400' : 'text-slate-600 group-hover:text-slate-400'}`} />
        <span className="text-[9px] font-bold uppercase tracking-wider truncate">{label}</span>
        {active && <motion.div layoutId="activeInd" className="ml-auto w-1 h-4 bg-indigo-500 rounded-full" />}
    </button>
);

const ControlToggle = ({ label, active, onClick, color = 'emerald' }) => (
    <button
        onClick={onClick}
        className={`relative px-4 py-1.5 h-[38px] min-w-fit whitespace-nowrap rounded-xl border transition-all duration-500 flex items-center gap-3 overflow-hidden group hover:scale-105 active:scale-95 cursor-pointer z-50 ${active
            ? `bg-${color}-500/10 border-${color}-500/30 shadow-[0_0_20px_rgba(16,185,129,0.2)]`
            : 'bg-white/5 border-white/10 hover:border-indigo-500/30 hover:bg-indigo-500/5'
            }`}
    >
        <div className={`w-2 h-2 rounded-full shadow-inner transition-colors duration-500 ${active ? `bg-${color}-400 shadow-[0_0_10px_currentColor] animate-pulse` : 'bg-slate-600'}`} />
        <span className={`text-[10px] font-black uppercase tracking-[0.2em] ${active ? 'text-white' : 'text-slate-400'}`}>
            {label}
        </span>
    </button>
);

// Agent Alignment Component
const AgentStatus = ({ label, status, icon: Icon, colorClass }) => {
    let containerClass = 'bg-white/2 border-white/5 opacity-40';
    let iconClass = 'text-slate-600';
    let textClass = 'text-slate-600';
    let dotClass = 'bg-slate-700';
    let glowStyle = {};

    if (status === 'AGREE') {
        containerClass = 'bg-emerald-500/10 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/20';
        iconClass = 'text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.5)]';
        textClass = 'text-emerald-400 font-black';
        dotClass = 'bg-emerald-400 animate-pulse-fast shadow-[0_0_10px_#10b981]';
        glowStyle = { textShadow: '0 0 10px rgba(16,185,129,0.3)' };
    } else if (status === 'DISAGREE') {
        containerClass = 'bg-red-500/10 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)] ring-1 ring-red-500/20';
        iconClass = 'text-red-500 drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]';
        textClass = 'text-red-500 font-black';
        dotClass = 'bg-red-500 animate-pulse-fast shadow-[0_0_10px_#ef4444]';
        glowStyle = { textShadow: '0 0 10px rgba(239,68,68,0.3)' };
    } else if (status === 'NEUTRAL') {
        containerClass = 'bg-slate-500/10 border-slate-500/30 shadow-[0_0_10px_rgba(100,116,139,0.1)] ring-1 ring-slate-500/20';
        iconClass = 'text-slate-400 drop-shadow-[0_0_5px_rgba(100,116,139,0.3)]';
        textClass = 'text-slate-400 font-black';
        dotClass = 'bg-slate-400 animate-pulse-slow shadow-[0_0_8px_#94a3b8]';
        glowStyle = { textShadow: '0 0 8px rgba(100,116,139,0.2)' };
    }

    return (
        <div
            className={`flex flex-col items-center justify-center gap-1.5 p-2.5 rounded-xl border transition-all duration-700 min-h-[64px] ${containerClass}`}
            style={glowStyle}
        >
            <Icon className={`w-4 h-4 transition-all duration-500 ${iconClass}`} />
            <span className={`text-[9px] uppercase tracking-widest transition-all duration-500 ${textClass}`}>{label}</span>
            <div className={`w-1.5 h-1.5 rounded-full transition-all duration-500 ${dotClass}`} />
        </div>
    );
};

const DashboardWithLogic = () => {
    const [activeTab, setActiveTab] = useState('Live Terminal');
    const [symbol, setSymbol] = useState('NSE:BANKNIFTY');
    const [searchInput, setSearchInput] = useState(symbol);
    const [data, setData] = useState({ price: 0, signal: 'HOLD', confidence: 0, status: 'NOMINAL', regime: 'NOMINAL' });
    const [analysis, setAnalysis] = useState(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isAutoMode, setIsAutoMode] = useState(false);
    const [chartData, setChartData] = useState([]);
    const [riskStatus, setRiskStatus] = useState({});
    const [optionChain, setOptionChain] = useState([]);
    const [orders, setOrders] = useState([]);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [token, setToken] = useState(null);
    const [showLogin, setShowLogin] = useState(true);
    const [showEmergencyConfirm, setShowEmergencyConfirm] = useState(false);
    const [showTrainingConfirm, setShowTrainingConfirm] = useState(false);
    const [showModeConfirm, setShowModeConfirm] = useState(false);
    const [dailyBias, setDailyBias] = useState({ bias: 'NEUTRAL', recommendation: 'Calibrating Strategist...', confidence: 0 });
    const [isBiasLoading, setIsBiasLoading] = useState(false);
    const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [terminalMode, setTerminalMode] = useState('TACTICAL'); // 'TACTICAL' or 'SWARM'
    const [toast, setToast] = useState(null);
    const [emergencyResult, setEmergencyResult] = useState(null);
    const [isLiquidating, setIsLiquidating] = useState(false);
    const isConfirmingRef = useRef(false);

    // Live Terminal Logging System
    const [terminalLogs, setTerminalLogs] = useState([
        { timestamp: new Date().toLocaleTimeString(), message: "Neural Command Center Online. V9.0 initializing...", type: 'system' }
    ]);

    const addTerminalLog = useCallback((message, type = 'system') => {
        const timestamp = new Date().toLocaleTimeString();
        setTerminalLogs(prev => [{ timestamp, message, type }, ...prev].slice(0, 50));
    }, []);

    const OWNER_EMAIL = "hari@tradeverse.ai";
    const [isOwner, setIsOwner] = useState(false);

    const [user, setUser] = useState({ name: 'Guest', initials: 'G', status: 'OFFLINE' });
    const [marketStatus, setMarketStatus] = useState({ isOpen: false, isHoliday: false, countdown: '00:00:00' });
    const [pipelineStats, setPipelineStats] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isTraining, setIsTraining] = useState(false);
    const [modelMetrics, setModelMetrics] = useState(null);
    const [trainingStatus, setTrainingStatus] = useState({
        is_training: false,
        progress: 0,
        stage: 'IDLE',
        message: 'No training in progress'
    });
    const [settings, setSettings] = useState({
        active_broker: 'ANGEL',
        angel_connected: false,
        env: 'MOCK'
    });
    // Load saved credentials from localStorage if available
    const loadSavedCredentials = () => {
        try {
            const saved = localStorage.getItem('tradeverse_credentials');
            if (saved) return JSON.parse(saved);
        } catch (e) {
            console.warn("Failed to load saved credentials", e);
        }
        return {
            angel_client_id: '', angel_password: '', angel_api_key: '', angel_totp_key: '',
            kite_api_key: '', kite_access_token: '',
            whatsapp_phone: '', whatsapp_api_key: '',
            telegram_bot_token: '', telegram_chat_id: ''
        };
    };

    const [activeSettingsTab, setActiveSettingsTab] = useState('API Keys');
    const [credentials, setCredentials] = useState(loadSavedCredentials());
    const [isConnecting, setIsConnecting] = useState(false);
    const [trustedIPs, setTrustedIPs] = useState([]);
    const [newIP, setNewIP] = useState('');
    const [systemStatus, setSystemStatus] = useState({ backend: false, intelligence: false });
    const [connCountdown, setConnCountdown] = useState(0);
    const [serverLatency, setServerLatency] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    const [scanProgress, setScanProgress] = useState(0);
    const abortControllerRef = useRef(null);

    const runSystemScan = () => {
        if (isScanning) return;
        setIsScanning(true);
        setScanProgress(0);

        let progress = 0;
        const interval = workerSetInterval(() => {
            progress += Math.floor(Math.random() * 15) + 5;
            if (progress >= 100) {
                progress = 100;
                workerClearInterval(interval);
                setTimeout(() => {
                    setIsScanning(false);
                    setScanProgress(0);
                }, 2000);
            }
            setScanProgress(progress);
        }, 300);
    };

    // --- GLOBAL API FETCH WRAPPER ---
    // Automatically handles 401 Unauthorized errors by forcefully refreshing the Firebase token
    // and retrying the request once. This prevents session expiry bugs.
    const apiFetch = async (url, options = {}) => {
        let currentToken = options.headers?.Authorization?.split(' ')[1] || token;

        let response = await fetch(url, options);

        if (response.status === 401 && auth?.currentUser) {
            console.warn(`[apiFetch] 401 Unauthorized on ${url}. Attempting to force-refresh Firebase token...`);
            try {
                // FORCE a refresh of the token
                const freshToken = await auth?.currentUser?.getIdToken(true);

                if (freshToken) {
                    console.log(`[apiFetch] Token refreshed successfully. Retrying request...`);
                    // Update React state and LocalStorage so subsequent calls use the new token
                    setToken(freshToken);
                    localStorage.setItem('authToken', freshToken);

                    // Update the headers for the retry
                    const newOptions = { ...options };
                    newOptions.headers = {
                        ...newOptions.headers,
                        'Authorization': `Bearer ${freshToken}`
                    };

                    // Retry the request
                    response = await fetch(url, newOptions);
                }
            } catch (refreshError) {
                console.error("[apiFetch] Token refresh failed:", refreshError);
                // The onIdTokenChanged listener or confirmLogout will handle kicking the user out
            }
        }

        return response;
    };

    // Save credentials to localStorage whenever they change
    useEffect(() => {
        try {
            localStorage.setItem('tradeverse_credentials', JSON.stringify(credentials));
        } catch (e) {
            console.warn("Failed to save credentials locally", e);
        }
    }, [credentials]);

    // Wake-up Ping on Mount
    useEffect(() => {
        const wakeUpBackend = async () => {
            // Only ping if not already connected/logged in to avoid redundant traffic
            if (isLoggedIn) return;

            console.log("Dashboard: Sending Wake-up Ping to Backend...");
            showToast("🚀 Initializing backend connection...", "info");

            try {
                // Simple HEAD or GET request to root/ping to wake up Render
                await fetch(`${API_URL}/api/ping`, { method: 'GET' });
                console.log("Dashboard: Backend Woken Up!");
                showToast("✅ Backend Online & Ready", "success");
                setSystemStatus(prev => ({ ...prev, backend: true }));
            } catch (e) {
                console.warn("Dashboard: Wake-up Ping failed (Backend might be sleeping deep)", e);
            }
        };

        wakeUpBackend();
    }, []);

    const checkServerHealth = async (retryCount = 0) => {
        setServerLatency("PINGING...");
        const start = Date.now();
        try {
            const res = await fetch(`${API_URL || '/backend-status'}/`, { method: 'GET', cache: 'no-store' });
            const latency = Date.now() - start;

            if (res.ok) {
                const data = await res.json();
                const intelligenceReady = data?.initialization?.ready || false;

                setServerLatency(`${latency}ms (ONLINE)`);
                setSystemStatus(prev => ({
                    ...prev,
                    backend: true,
                    intelligence: intelligenceReady
                }));
            } else if ((res.status === 502 || res.status === 503) && retryCount < 3) {
                // Render Hibernation / Startup Handshake phase
                setServerLatency(`WAKING UP (${retryCount + 1})...`);
                setTimeout(() => checkServerHealth(retryCount + 1), 3000);
            } else {
                setServerLatency(`Error ${res.status}`);
                setSystemStatus(prev => ({ ...prev, backend: false }));
            }
        } catch (e) {
            if (retryCount < 2) {
                setServerLatency("RETRYING...");
                setTimeout(() => checkServerHealth(retryCount + 1), 2000);
            } else {
                setServerLatency("UNREACHABLE");
                setSystemStatus(prev => ({ ...prev, backend: false }));
            }
        }
    };

    const showToast = (message, type = 'info') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 4000);
    };

    const playInitSound = () => {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.3);
    };

    const getAgentStatus = (agent) => {
        if (!analysis) return 'IDLE';

        // Map individual agent recommendations to lights:
        // AGREE = Bullish (Green), DISAGREE = Bearish (Red), NEUTRAL = Idle (Grey)

        if (agent === 'TECH') {
            const pred = analysis.ai_prediction || 'NEUTRAL';
            if (pred === 'UP') return 'AGREE';
            if (pred === 'DOWN') return 'DISAGREE';
            return 'NEUTRAL';
        }
        if (agent === 'TFT') {
            const pred = analysis.tft_prediction || 'NEUTRAL';
            if (pred === 'UP') return 'AGREE';
            if (pred === 'DOWN') return 'DISAGREE';
            return 'NEUTRAL';
        }
        if (agent === 'RL') {
            const action = analysis.rl_action; // 1: BUY, 2: SELL, 0: HOLD
            if (action === 1) return 'AGREE';
            if (action === 2) return 'DISAGREE';
            return 'NEUTRAL';
        }
        if (agent === 'SENT') {
            const label = analysis.sentiment_label || 'NEUTRAL';
            if (label === 'POSITIVE') return 'AGREE';
            if (label === 'NEGATIVE') return 'DISAGREE';
            return 'NEUTRAL';
        }
        if (agent === 'OPT') {
            const pcr = analysis.pcr;
            if (pcr === undefined || (pcr >= 0.9 && pcr <= 1.1)) return 'NEUTRAL';
            return (pcr < 0.9) ? 'AGREE' : 'DISAGREE'; // PCR <0.9 is Bullish
        }

        return 'IDLE';
    };

    const handleUpdateCredentials = async () => {
        setIsConnecting(true);
        setConnCountdown(90); // Increased to 90s to account for Render cold start

        const controller = new AbortController();
        abortControllerRef.current = controller;
        const timeoutId = setTimeout(() => controller.abort(), 90000); // Unified 90s timeout

        // Countdown interval
        const timerId = workerSetInterval(() => {
            setConnCountdown(prev => {
                if (prev <= 1) {
                    workerClearInterval(timerId);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        const wakeUpToastId = setTimeout(() => {
            if (!systemStatus.backend) {
                showToast("⏳ Waking up server... (this may take a minute)", "info");
            }
        }, 4000); // Slightly faster check

        try {
            const payload = { ...credentials, active_broker: 'ANGEL' };
            const res = await apiFetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'ngrok-skip-browser-warning': 'true', // Bypasses ngrok warning
                    'Bypass-Tunnel-Reminder': 'true' // Bypasses localtunnel/pinggy warning
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            workerClearInterval(timerId);
            clearTimeout(timeoutId);
            clearTimeout(wakeUpToastId);

            if (!res.ok) throw new Error(`Server returned ${res.status}`);

            const data = await res.json();
            if (data.status === 'success') {
                if (data.broker_connected) {
                    showToast("Credentials Updated & Connected to Angel One!", "success");
                    addTerminalLog("CONNECTION: Angel One API handshake successful. Live stream established.", "system");
                    // Auto-switch to LIVE mode
                    setSettings(prev => ({
                        ...prev,
                        active_broker: 'ANGEL',
                        angel_connected: true,
                        env: 'LIVE'
                    }));
                    setUser({ name: 'Pro Trader', initials: 'PT', status: 'ONLINE', broker: 'ANGEL ONE' });

                    // Trigger backend to update env to LIVE as well
                    fetch(`${API_URL}/api/settings/update`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ env: 'LIVE' })
                    }).catch(e => console.error("Auto-Live Switch Failed", e));

                } else {
                    const eMsg = data.error || "Check logs";
                    showToast(`Connection Failed: ${eMsg}`, "error");
                    addTerminalLog(`CONNECTION ERROR: ${eMsg}`, "error");
                }
            } else {
                showToast(data.message || "Update Failed", "error");
                addTerminalLog("SYSTEM: API configuration update failed.", "error");
            }
        } catch (e) {
            workerClearInterval(timerId);
            clearTimeout(wakeUpToastId); // Ensure wake toast timer is cleared on error
            if (e.name === 'AbortError') {
                showToast(connCountdown > 0 ? "Connection Cancelled" : "Connection Timed Out (90s)", "error");
                addTerminalLog("SYSTEM: Connection attempt timed out.", "error");
            } else {
                console.error("Credential Update Error:", e);
                showToast(`Network Error: ${e.message}`, "error");
                addTerminalLog(`NETWORK: ${e.message}`, "error");
            }
        } finally {
            setIsConnecting(false);
            setConnCountdown(0);
            clearTimeout(timeoutId);
            clearTimeout(wakeUpToastId);
            workerClearInterval(timerId);
            abortControllerRef.current = null;
        }
    };

    const handleAngelDisconnect = async () => {
        setShowDisconnectConfirm(false);
        setIsConnecting(true);
        try {
            const res = await fetch(`${API_URL}/api/settings/disconnect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ broker: 'ANGEL' })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast("Angel One Disconnected. Reverted to Mock mode.", "success");
                setSettings(prev => ({
                    ...prev,
                    active_broker: data.active_broker,
                    angel_connected: false,
                    angel_credentials: null
                }));
            }
        } catch (e) {
            showToast("Server Error during disconnect.", "error");
        }
        setIsConnecting(false);
    };

    const handleEmergencyStop = useCallback(() => {
        console.log("Dashboard: Opening Emergency Modal...");
        setShowEmergencyConfirm(true);
    }, []);

    const executeEmergencyProtocol = async () => {
        setIsLiquidating(true);
        setEmergencyResult(null);
        console.log("Dashboard: Executing Emergency Protocol...");
        try {
            const res = await fetch(`${API_URL}/api/broker/emergency`, {
                method: "POST",
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                console.log("Dashboard: Emergency Protocol Success");
                setEmergencyResult({ success: true, message: data.message });
                setIsAutoMode(false);
                addTerminalLog(`PROTOCOL DELTA: ${data.message}`, "error");
            } else {
                console.error("Dashboard: Emergency Protocol Failed", data);
                const eMsg = data.detail || data.message || "Liquidation Failed";
                setEmergencyResult({
                    success: false,
                    message: eMsg
                });
                addTerminalLog(`CRITICAL FAILURE: Emergency Protocol - ${eMsg}`, "error");
            }
        } catch (e) {
            console.error("Dashboard: Emergency Protocol Connection Error", e);
            setEmergencyResult({
                success: false,
                message: "CRITICAL CONNECTION ERROR during Emergency Stop"
            });
            addTerminalLog("CRITICAL: Network failure during emergency protocol execution!", "error");
        } finally {
            setIsLiquidating(false);
        }
    };

    const fetchSettings = async (overrideToken = null) => {
        try {
            const headers = {};
            const activeToken = overrideToken || token;
            if (activeToken) {
                headers['Authorization'] = `Bearer ${activeToken}`;
            }
            const res = await apiFetch(`${API_URL}/api/settings`, { headers });

            if (res.status === 401) {
                console.warn("fetchSettings: Unauthorized after retry. Logging out.");
                return;
            }

            const data = await res.json();
            setSettings(prev => ({
                ...prev,
                active_broker: data.active_broker,
                env: data.env,
                zerodha_connected: data.zerodha_connected,
                angel_connected: data.angel_connected
            }));
            setIsAutoMode(data.mode === 'AUTO');
            if (data.serverLatency) setServerLatency(data.serverLatency);

            if (data.angel_credentials) {
                setCredentials(prev => ({
                    ...prev,
                    ...data.angel_credentials,
                    ...data.whatsapp_credentials,
                    ...data.telegram_credentials
                }));
            }
        } catch (e) { console.error("Settings Fetch Failed", e); }
    };

    const fetchTrustedIPs = async () => {
        try {
            const res = await apiFetch(`${API_URL}/api/settings/trusted-ips`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                setTrustedIPs(data.trusted_ips);
            }
        } catch (e) { console.error("Trusted IPs Fetch Failed", e); }
    };

    const fetchSystemStatus = async () => {
        try {
            const res = await fetch(`${API_URL || '/backend-status'}/`);
            const data = await res.json();
            setSystemStatus({
                backend: true,
                intelligence: data.initialization?.ready || false
            });
        } catch (e) {
            console.error("System Status Fetch Failed:", e);
            setSystemStatus({ backend: false, intelligence: false });
        }
    };

    const handleAddTrustedIP = async () => {
        if (!newIP.trim()) return;
        try {
            const res = await apiFetch(`${API_URL}/api/settings/trusted-ips/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ip_address: newIP.trim() })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(data.message, 'success');
                setNewIP('');
                fetchTrustedIPs();
            } else {
                showToast(data.detail || 'Invalid IP format', 'error');
            }
        } catch (e) {
            showToast('Failed to add IP', 'error');
        }
    };

    const handleRemoveTrustedIP = async (ip) => {
        try {
            const res = await apiFetch(`${API_URL}/api/settings/trusted-ips/remove`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ ip_address: ip })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(data.message, 'success');
                fetchTrustedIPs();
            }
        } catch (e) {
            showToast('Failed to remove IP', 'error');
        }
    };

    const handleBrokerSwitch = async (broker) => {
        try {
            const res = await apiFetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ active_broker: broker })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setSettings(prev => ({
                    ...prev,
                    active_broker: data.active_broker,
                    broker_connected: data.broker_connected,
                    env: data.env
                }));
            }
        } catch (e) {
            console.error("Broker Switch Failed", e);
        }
    };

    const handleEnvSwitch = async (env) => {
        console.log(`[HANDLE_ENV_SWITCH] Attempting to switch to: ${env}`);

        // Environment Switch
        if (env === 'LIVE' && !isOwner) {
            console.log("[HANDLE_ENV_SWITCH] Non-owner attempting LIVE switch. Proceeding with user-isolated mode.");
        }

        // If switching to LIVE but not connected or guest, prompt for login
        if (env === 'LIVE') {
            if (!isLoggedIn || user.status === 'GUEST') {
                console.log("[HANDLE_ENV_SWITCH] Blocked: Guest User. prompting Login.");
                setShowLogin(true);
                return;
            }

            if (!settings.angel_connected) {
                console.log("[HANDLE_ENV_SWITCH] Blocked: Not connected to Angel One.");
                const shouldLogin = window.confirm("Live Trading requires an active Angel One connection.\n\nClick OK to go to Settings and login.");

                if (shouldLogin) {
                    console.log("[HANDLE_ENV_SWITCH] Redirecting to Settings> API Keys");
                    setActiveTab('Settings');
                    setActiveSettingsTab('API Keys');
                }
                return;
            }
        }

        try {
            const res = await apiFetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ env: env })
            });
            const data = await res.json();
            if (data.status === 'success') {
                setSettings(prev => ({
                    ...prev,
                    env: data.env,
                    broker_connected: data.broker_connected
                }));

                // If switching to MOCK, automatically logout and go to guest mode
                if (env === 'MOCK') {
                    console.log("Switching to MOCK: Activating Guest Mode");
                    await confirmLogout();
                    handleGuestLogin();
                }
            }
        } catch (e) {
            console.error("Env Update Failed", e);
        }
    };

    const handleModeToggle = useCallback(async () => {
        // Mode Toggle
        if (!isOwner) {
            console.log("[HANDLE_MODE_TOGGLE] Non-owner attempting Auto-Pilot switch.");
        }

        const nextMode = isAutoMode ? 'MANUAL' : 'AUTO';

        if (nextMode === 'AUTO') {
            setShowModeConfirm(true);
            return;
        }

        await executeModeSwitch('MANUAL');
    }, [isAutoMode]);

    const handleUpdateWhatsAppSettings = async () => {
        setIsConnecting(true);
        try {
            const res = await apiFetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    whatsapp_phone: credentials.whatsapp_phone,
                    whatsapp_api_key: credentials.whatsapp_api_key
                })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast("WhatsApp Settings Saved!", "success");
            }
        } catch (e) {
            showToast("Failed to save settings", "error");
        }
        setIsConnecting(false);
    };

    const handleUpdateTelegramSettings = async () => {
        setIsConnecting(true);
        try {
            const res = await apiFetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    telegram_bot_token: credentials.telegram_bot_token,
                    telegram_chat_id: credentials.telegram_chat_id
                })
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast("Telegram Settings Saved!", "success");
            }
        } catch (e) {
            showToast("Failed to save settings", "error");
        }
        setIsConnecting(false);
    };

    const handleSendTestWhatsApp = async () => {
        setIsConnecting(true);
        try {
            const res = await apiFetch(`${API_URL}/api/settings/whatsapp/test`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(data.message || "Test message sent!", "success");
            } else {
                showToast(data.message || "Failed to send test message.", "error");
            }
        } catch (e) {
            showToast("Server Error", "error");
        }
        setIsConnecting(false);
    };

    const handleSendTestTelegram = async () => {
        setIsConnecting(true);
        try {
            const res = await apiFetch(`${API_URL}/api/settings/telegram/test`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                showToast(data.message || "Test message sent!", "success");
            } else {
                showToast(data.message || "Failed to send test message.", "error");
            }
        } catch (e) {
            showToast("Server Error", "error");
        }
        setIsConnecting(false);
    };

    const executeModeSwitch = async (targetMode) => {
        const previousAuto = isAutoMode;
        console.log(`[MODE_TOGGLE] Executing switch to ${targetMode}`);

        setIsAutoMode(targetMode === 'AUTO');
        setShowModeConfirm(false);

        try {
            const res = await apiFetch(`${API_URL}/api/settings/mode`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ mode: targetMode })
            });

            if (!res.ok) throw new Error(`HTTP Error ${res.status}`);

            const data = await res.json();
            if (data.status !== 'success') {
                throw new Error(data.message || 'Mode switch failed');
            }

            if (data.mode) {
                setIsAutoMode(data.mode === 'AUTO');
            }
        } catch (e) {
            console.error("[MODE_TOGGLE] Error:", e);
            setIsAutoMode(previousAuto);
            alert(`Critical Error: ${e.message}`);
        }
    };

    const [params, setParams] = useState({
        multiplier: 3.0,
        adx: 25,
        rsi: 14,
        target: 0.3
    });

    // Sub-Interval Timestamp Tracker Updates
    const [lastPriceUpdate, setLastPriceUpdate] = useState(new Date());
    const [lastOptionUpdate, setLastOptionUpdate] = useState(new Date());
    const [lastAnalysisUpdate, setLastAnalysisUpdate] = useState(new Date());

    const [searchResults, setSearchResults] = useState([]);
    const [showResults, setShowResults] = useState(false);

    // Restore token from localStorage on mount
    useEffect(() => {
        const savedToken = localStorage.getItem('authToken');
        if (savedToken) {
            setToken(savedToken);
            setIsLoggedIn(true);
            setShowLogin(false);
            setUser({ name: 'Guest Trader', initials: 'G', status: 'GUEST' });

            // Detect owner on mount
            if (savedToken === 'mock-token-123' || auth?.currentUser?.email?.toLowerCase() === OWNER_EMAIL) {
                setIsOwner(true);
            }
        }
    }, []);

    // Also watch auth state for changes and auto-refresh token
    useEffect(() => {
        const unsubscribe = auth?.onIdTokenChanged(async (user) => {
            if (user) {
                if (user.email?.toLowerCase() === OWNER_EMAIL) {
                    setIsOwner(true);
                } else {
                    setIsOwner(false);
                }

                try {
                    // Firebase automatically refreshes the token behind the scenes.
                    // This listener fires whenever the token changes (or auth state changes).
                    const freshToken = await user.getIdToken();
                    if (freshToken) {
                        setToken(freshToken);
                        localStorage.setItem('authToken', freshToken);
                    }
                } catch (err) {
                    console.error("Error refreshing Firebase token:", err);
                }
            } else if (localStorage.getItem('authToken') !== 'mock-token-123') {
                setIsOwner(false);
            }
        });
        return () => unsubscribe && unsubscribe();
    }, []);

    // Sync User Profile with Environment Settings
    useEffect(() => {
        if (settings.env === 'MOCK') {
            setUser({ name: 'Guest Trader', initials: 'G', status: 'GUEST' });
        } else if (settings.env === 'LIVE' && settings.angel_connected) {
            setUser({ name: 'Pro Trader', initials: 'PT', status: 'ONLINE', broker: 'ANGEL ONE' });
        }
    }, [settings.env, settings.angel_connected]);

    useEffect(() => {
        let intervalId;

        if (isAutoMode && token) {
            const sendHeartbeat = async () => {
                try {
                    await fetch(`${API_URL}/api/monitoring/heartbeat`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                } catch (e) {
                    console.error("Heartbeat Failed:", e);
                }
            };

            sendHeartbeat();
            intervalId = workerSetInterval(sendHeartbeat, 5000);
            addTerminalLog("Autopilot Heartbeat Active. System synced with cloud sentinel.", "system");
        } else if (token) {
            addTerminalLog("Manual Control Mode Engage.", "system");
        }

        return () => workerClearInterval(intervalId);
    }, [isAutoMode, token]);

    // System Event Observers
    useEffect(() => {
        if (data.regime && data.regime !== 'NOMINAL') {
            addTerminalLog(`MARKET ALERT: Structural Regime Shift -> ${data.regime}`, 'error');
        }
    }, [data.regime]);

    useEffect(() => {
        if (analysis?.sentiment_label) {
            const color = analysis.sentiment_label === 'POSITIVE' ? 'text-emerald-400' : analysis.sentiment_label === 'NEGATIVE' ? 'text-rose-400' : 'text-slate-400';
            addTerminalLog(`SENTIMENT: News & Social Media analysis detected ${analysis.sentiment_label} mood.`, 'sentiment');
        }
    }, [analysis?.sentiment_label]);

    useEffect(() => {
        if (data.signal !== 'HOLD') {
            addTerminalLog(`SIGNAL UPDATE: Neural consensus favors ${data.signal} for ${symbol}.`, 'signal');
        }
    }, [data.signal, symbol]);

    useEffect(() => {
        const timer = setTimeout(async () => {
            if (searchInput.length >= 3) {
                try {
                    const res = await fetch(`${API_URL}/api/market/search?query=${searchInput}`);
                    const data = await res.json();
                    if (Array.isArray(data)) {
                        setSearchResults(data);
                        setShowResults(true);
                    }
                } catch (e) { console.error("Search error", e); }
            } else {
                setSearchResults([]);
                setShowResults(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchInput]);

    const selectSymbol = (sym) => {
        setSymbol(sym);
        setSearchInput(sym);
        setChartData([]);
        setShowResults(false);
    };

    const navItems = [
        { icon: Terminal, label: 'Live Terminal' },
        { icon: Layers, label: 'Option Chain & GEX' },
        { icon: ListOrdered, label: 'Orders' },
        { icon: ScrollText, label: 'Simulations' },
        { icon: Telescope, label: 'Observatory' },
        { icon: GraduationCap, label: 'Strategies' },
        { icon: Database, label: 'Backtest' },
        { icon: BarChart3, label: 'Analytics' },
        { icon: Lightbulb, label: 'INSIGHTS' },
        { icon: Briefcase, label: 'Smallcases' },
        { icon: Activity, label: 'Market Pulse' },
        { icon: LayoutDashboard, label: 'Portfolio' },
        { icon: HeartPulse, label: 'System Health' },
        { icon: BookOpen, label: 'Lessons Learned' },
        { icon: Settings, label: 'Settings' },
    ];

    useEffect(() => {
        console.log("Dashboard: Component MOUNTED");
        return () => console.log("Dashboard: Component UNMOUNTED");
    }, []);

    useEffect(() => {
        let priceInterval, optionsInterval, timerInterval, biasInterval;
        if (isLoggedIn) {
            fetchStatus();
            fetchSettings();
            calculateMarketStatus();
            fetchDailyBias();

            // Immediate fetch on symbol change
            fetchPrice();
            fetchOptionChain();

            priceInterval = workerSetInterval(fetchPrice, 3000);
            optionsInterval = workerSetInterval(fetchOptionChain, 5000);
            timerInterval = workerSetInterval(calculateMarketStatus, 1000);
            biasInterval = workerSetInterval(fetchDailyBias, 3600000); // Hourly refresh
        }

        return () => {
            if (priceInterval) workerClearInterval(priceInterval);
            if (optionsInterval) workerClearInterval(optionsInterval);
            if (timerInterval) clearInterval(timerInterval);
            if (biasInterval) workerClearInterval(biasInterval);
        };
    }, [symbol, isLoggedIn]);

    useEffect(() => {
        let autoInterval;
        if (isLoggedIn && isAutoMode) {
            autoInterval = workerSetInterval(executeAutoPilot, 30000);
        } return () => {
            if (autoInterval) workerClearInterval(autoInterval);
        };
    }, [isAutoMode, isLoggedIn, symbol]);

    const calculateMarketStatus = () => {
        const now = new Date();
        const day = now.getDay();
        const isWeekend = day === 0 || day === 6;

        const holidays = [
            '2026-01-26', // Republic Day
            '2026-03-03', // Holi
            '2026-03-17', // Mahashivratri
            '2026-04-02', // Mahavir Jayanti
            '2026-04-03', // Good Friday
            '2026-04-14', // Ambedkar Jayanti
            '2026-05-01', // Maharashtra Day
            '2026-08-15', // Independence Day
            '2026-10-02', // Gandhi Jayanti
            '2026-12-25'  // Christmas
        ];
        const localDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        const isHoliday = holidays.includes(localDate);

        const openTime = new Date(now);
        openTime.setHours(9, 15, 0, 0);

        const closeTime = new Date(now);
        closeTime.setHours(15, 30, 0, 0);

        let isOpen = !isWeekend && !isHoliday && now >= openTime && now <= closeTime;

        let target;
        if (isOpen) {
            target = closeTime;
        } else {
            target = new Date(now);
            // If holiday or weekend or after 3:30, find next open
            let checkDate = new Date(now);
            if (now > closeTime || isWeekend || isHoliday) {
                // Find nearest working day
                let found = false;
                let safety = 0;
                while (!found && safety < 10) {
                    checkDate.setDate(checkDate.getDate() + 1);
                    const checkDay = checkDate.getDay();
                    const checkDateStr = `${checkDate.getFullYear()}-${String(checkDate.getMonth() + 1).padStart(2, '0')}-${String(checkDate.getDate()).padStart(2, '0')}`;
                    if (checkDay !== 0 && checkDay !== 6 && !holidays.includes(checkDateStr)) {
                        found = true;
                    }
                    safety++;
                }
            }
            target = new Date(checkDate);
            target.setHours(9, 15, 0, 0);
        }

        const diff = target - now;
        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);

        setMarketStatus({
            isOpen,
            isHoliday,
            countdown: `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
        });
    };

    const fetchStatus = async () => {
        try {
            // Fetch Risk Status
            const resRisk = await fetch(`${API_URL}/api/risk/status`);
            if (resRisk.ok) {
                const risk = await resRisk.json();
                if (risk) setRiskStatus(risk);
            }

            // Fetch System Initialization Status (Intelligence & Backend)
            const resInit = await fetch(`${API_URL || '/backend-status'}/`);
            if (resInit.ok) {
                const initData = await resInit.json();
                setSystemStatus({
                    backend: true,
                    intelligence: initData.initialization?.ready || false
                });
            } else {
                setSystemStatus({ backend: true, intelligence: false }); // Backend reachable but returned error
            }
        } catch (e) {
            // If fetch fails completely, backend is likely down
            setSystemStatus({ backend: false, intelligence: false });
        }
    };

    const fetchPrice = async () => {
        try {
            const res = await fetch(`${API_URL}/api/market/ltp/${symbol}`);
            if (!res.ok) return; // Skip if backend fails
            const info = await res.json();

            // Validate data before state update
            if (info && info.last_price !== undefined) {
                setData(prev => ({ ...prev, price: info.last_price }));
                setChartData(prev => {
                    // Keep chart data array size manageable
                    const newData = [...prev, { time: new Date().toLocaleTimeString(), price: info.last_price }];
                    if (newData.length > 50) return newData.slice(-50);
                    return newData;
                });
                setLastPriceUpdate(new Date());
            }
        } catch (e) {
            // Silent fail for polling errors to prevent UI crash
            // console.warn("Price Fetch Failed");
        }
    };

    const fetchOptionChain = async () => {
        try {
            const res = await fetch(`${API_URL}/api/market/options/${symbol}`);
            if (!res.ok) return;
            const info = await res.json();
            // Ensure info is an array
            if (Array.isArray(info)) {
                setOptionChain(info);
                setLastOptionUpdate(new Date());
            }
        } catch (e) {
            // console.warn("Options Fetch Failed");
        }
    };

    const runAgentAnalysis = async () => {
        if (!isLoggedIn) return;
        setIsAnalyzing(true);
        addTerminalLog(`Initiating Swarm Intelligence scan for ${symbol}...`, 'ai');
        try {
            const res = await apiFetch(`${API_URL}/api/intelligence/analyze/${symbol}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ positions: [] })
            });
            const result = await res.json();
            setAnalysis(result);
            // Extract Greeks from technical context
            const techCtx = result.technical_context || {};
            const rawGreeks = techCtx.greeks || {};

            // Map directional delta (CE vs PE)
            const isPut = result.final_signal === 'SELL';
            const directionalDelta = isPut ? Math.abs(rawGreeks.pe_delta || 0) : (rawGreeks.ce_delta || 0);

            setData(prev => ({
                ...prev,
                signal: result.final_signal,
                confidence: result.confidence,
                regime: result.regime || 'NOMINAL',
                trade_recommendation: result.trade_recommendation,
                greeks: {
                    delta: directionalDelta || 0.5,
                    gamma: rawGreeks.gamma || 0.004,
                    theta: rawGreeks.theta || -12,
                    vega: rawGreeks.vega || 40,
                    iv: rawGreeks.iv || 15
                }
            }));
            
            setLastAnalysisUpdate(new Date());

            if (result.final_signal !== 'HOLD') {
                addTerminalLog(`CRITICAL: Signal generated -> ${result.final_signal} (${result.confidence}%)`, 'signal');
                addTerminalLog(`Reasoning: ${result.trade_recommendation?.reasoning || 'Alpha alignment confirmed.'}`, 'ai');
            } else {
                addTerminalLog(`Scan complete: No actionable divergence detected.`, 'system');
            }

        } catch (e) {
            console.error("Analysis Failed", e);
            addTerminalLog(`ERROR: Intelligence scan aborted. Check backend latency.`, 'error');
        }
        setIsAnalyzing(false);
    };

    const fetchDailyBias = async () => {
        setIsBiasLoading(true);
        try {
            const res = await apiFetch(`${API_URL}/api/intelligence/daily-bias`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const result = await res.json();
            setDailyBias(result);
        } catch (e) {
            console.error("Daily Bias Fetch Failed", e);
        }
        setIsBiasLoading(false);
    };

    const executeAutoPilot = async () => {
        if (!isLoggedIn || !marketStatus.isOpen) return;
        setIsAnalyzing(true);
        console.log("AUTO-PILOT: Initiating Analysis & Execution Cycle...");
        try {
            const res = await apiFetch(`${API_URL}/api/trading/autopilot`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ symbol: symbol, quantity: 1 })
            });
            const result = await res.json();

            // Result: { status, order_id, signal, analysis, reason }

            if (result.analysis) {
                setAnalysis(result.analysis);
                setData(prev => ({
                    ...prev,
                    signal: result.analysis.final_signal,
                    confidence: result.analysis.confidence,
                    regime: result.analysis.regime || 'NOMINAL',
                    trade_recommendation: result.analysis.trade_recommendation
                }));
            }

            if (result.status === 'EXECUTED') {
                console.log(`AUTO-PILOT: Order Executed! ID: ${result.order_id}`);
                addTerminalLog(`EXECUTION: Order ${result.order_id} filled successfully.`, 'signal');
            } else if (result.status === 'IGNORED') {
                addTerminalLog(`PILOT: Opportunity bypassed - filter criteria not met.`, 'system');
            } else if (result.status === 'ERROR') {
                addTerminalLog(`EXECUTION ERROR: ${result.reason || 'Unknown error'}`, 'error');
            } else if (result.status === 'HOLD') {
                console.log(`AUTO-PILOT: Hold Signal. Reason: ${result.reason}`);
                addTerminalLog(`PILOT: Hold Signal. Reason: ${result.reason}`, 'system');
            }
            // Refresh orders to show the new trade, regardless of execution status
            fetchOrders();

        } catch (e) {
            console.error("AutoPilot Execution Failed", e);
        }
        setIsAnalyzing(false);
    };

    const handleLogin = (e) => {
        e.preventDefault();
        setIsLoggedIn(true);
        setShowLogin(false);
        setUser({ name: 'Pro Trader', initials: 'P', status: 'ONLINE' });
        // Ensure token persistence safely handles fallback events
        if (token) localStorage.setItem('authToken', token);
    };

    const confirmLogout = async () => {
        setShowLogoutConfirm(false);
        try {
            console.log("Dashboard: Calling logout API...");
            await apiFetch(`${API_URL}/api/auth/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
        } catch (e) {
            console.error("Dashboard: Logout API failed", e);
        }

        console.log("Dashboard: Resetting auth state...");
        setIsLoggedIn(false);
        setUser({ name: 'Guest', initials: 'G', status: 'OFFLINE' });
        setShowLogin(true);
    };

    const handleLogout = () => {
        setShowLogoutConfirm(true);
    };

    const handleGuestLogin = () => {
        const mockToken = 'mock-token-123';
        setIsLoggedIn(true);
        setShowLogin(false);
        setToken(mockToken); // Set mock token for guest access
        localStorage.setItem('authToken', mockToken); // Persist token in localStorage
        setUser({ name: 'Guest Trader', initials: 'G', status: 'GUEST' });

        const fetchSettingsLocal = async (overrideToken = null) => {
            try {
                const res = await apiFetch(`${API_URL}/api/settings`, {
                    headers: { 'Authorization': `Bearer ${overrideToken || token}` }
                });
                const data = await res.json();
                if (data.serverLatency) setServerLatency(data.serverLatency);

                // Auto-Revert Logic: If backend says LIVE but no connection, force MOCK
                let effectiveEnv = data.env;
                if (data.env === 'LIVE' && !data.angel_connected) {
                    console.warn("State Mismatch: ENV=LIVE but Angel Not Connected. Reverting to MOCK.");
                    effectiveEnv = 'MOCK';

                    // Sync backend asynchronously
                    apiFetch(`${API_URL}/api/settings/update`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${overrideToken || token}`
                        },
                        body: JSON.stringify({ env: 'MOCK' })
                    });
                }

                setSettings({
                    angel_connected: data.angel_connected,
                    active_broker: data.active_broker,
                    env: effectiveEnv
                });

                // Update User Profile based on effective Env
                if (effectiveEnv === 'MOCK') {
                    setUser({ name: 'Guest Trader', initials: 'G', status: 'GUEST' });
                } else if (effectiveEnv === 'LIVE' && data.angel_connected) {
                    setUser({ name: 'Pro Trader', initials: 'PT', status: 'ONLINE', broker: 'ANGEL ONE' });
                }

            } catch (e) { console.error("Settings Fetch Failed", e); }
        };

        fetchSettingsLocal(mockToken);
    };

    const handleTriggerTraining = async () => {
        setShowTrainingConfirm(false);
        setIsTraining(true); // Immediate feedback
        try {
            const res = await apiFetch(`${API_URL}/api/ai/train`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || "Training trigger failed");
            }

            const result = await res.json();
            if (result.status === 'started') {
                showToast("🧠 AI Swarm Retraining Started!", "success");
                // Start polling for status
                pollTrainingStatus();
            } else {
                throw new Error("Training failed to start");
            }
        } catch (e) {
            console.error("Training Trigger Failed", e);
            setIsTraining(false); // Revert state on failure
            showToast(e.message || "Failed to start training", "error");
        }
    };

    const pollTrainingStatus = async () => {
        let errorCount = 0;
        let attempts = 0;
        const maxAttempts = 450; // ~15 minutes at 2s interval

        const interval = workerSetInterval(async () => {
            attempts++;
            try {
                const res = await apiFetch(`${API_URL}/api/ai/train/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!res.ok) throw new Error("Status check failed");

                const status = await res.json();
                setTrainingStatus(status);
                errorCount = 0; // Reset on success

                if (!status.is_training) {
                    workerClearInterval(interval);
                    setIsTraining(false);

                    if (status.stage === 'COMPLETE') {
                        showToast("✅ AI Swarm Rebuild Complete!", "success");
                        setModelMetrics(status.metrics);
                    } else if (status.stage === 'ERROR') {
                        showToast("❌ Training Failed: " + (status.message || "Unknown Error"), "error");
                    }
                }
            } catch (e) {
                console.error("Status Poll Failed", e);
                errorCount++;
                if (errorCount >= 5) {
                    workerClearInterval(interval);
                    setIsTraining(false);
                    setTrainingStatus(prev => ({ ...prev, stage: 'ERROR', message: 'Connection lost during training' }));
                    showToast("❌ Training Status Connection Lost", "error");
                }
            }

            if (attempts >= maxAttempts) {
                workerClearInterval(interval);
                setIsTraining(false);
                setTrainingStatus(prev => ({ ...prev, stage: 'ERROR', message: 'Training timed out' }));
                showToast("❌ Training Timed Out", "error");
            }
        }, 2000); // Poll every 2 seconds
    };

    const handleTrainModel = handleTriggerTraining; // Backwards compatibility

    const fetchOrders = async () => {
        try {
            const res = await fetch(`${API_URL}/api/orders`);
            const data = await res.json();
            if (Array.isArray(data)) {
                setOrders(data);
            }
        } catch (e) { console.error("Orders Fetch Failed", e); }
    };

    const placeTestOrder = async () => {
        const symbol = prompt("Enter Symbol for TEST MARKET BUY (Intraday):", "BANKNIFTY");
        if (!symbol) return;

        const qty = symbol.toUpperCase() === "BANKNIFTY" ? 15 : 1;

        if (!window.confirm(`Place a TEST MARKET BUY order for ${symbol} (Qty: ${qty})?`)) return;

        try {
            const res = await fetch(`${API_URL}/api/order/place`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tradingsymbol: symbol.toUpperCase(),
                    transaction_type: "BUY",
                    quantity: qty,
                    exchange: "NSE",
                    product: "MIS",
                    order_type: "MARKET"
                })
            });
            const data = await res.json();
            if (data.status === "COMPLETE" || data.order_id) {
                alert(`Order Placed! ID: ${data.order_id}`);
                // Refresh orders after short delay
                setTimeout(fetchOrders, 2000);
            } else {
                alert(`Order Failed: ${data.reason || JSON.stringify(data)}`);
            }
        } catch (e) {
            alert(`Execution Error: ${e.message}`);
        }
    };

    useEffect(() => {
        if (activeTab === 'Orders') {
            fetchOrders();
            const interval = workerSetInterval(fetchOrders, 5000);
            return () => workerClearInterval(interval);
        }
    }, [activeTab]);

    const handleTabChange = (tabLabel) => {
        // IP Protection: Backup Tab Restriction
        if (tabLabel === 'Settings' && !isOwner) {
            // Allow access to settings for everyone for login/broker setup
        }

        const ALLOWED_MOCK_TABS = ['Live Terminal', 'Settings', 'Backtest', 'Strategies', 'Analytics', 'INSIGHTS', 'Simulations', 'Observatory', 'Lessons Learned'];

        if (settings.env === 'MOCK' && !ALLOWED_MOCK_TABS.some(t => t.toUpperCase() === tabLabel.toUpperCase())) {
            console.log(`[TAB_RESTRICTION] Blocked access to ${tabLabel} in MOCK mode.`);
            setShowLogin(true);
            return;
        }
        if (tabLabel === 'Settings') {
            checkServerHealth();
        }
        setActiveTab(tabLabel);
        setIsDrawerOpen(false); // Close drawer on tab change
    };

    return (
        <div className="flex flex-col lg:flex-row h-screen bg-[#0c0d12] text-white font-sans overflow-hidden selection:bg-indigo-500/30">
            {/* Mobile Bottom Navigation */}
            <nav className="fixed bottom-6 left-4 right-4 z-[100] h-16 glass-premium border border-white/10 rounded-3xl flex items-center justify-around px-4 lg:hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                {[
                    { icon: Terminal, label: 'Live Terminal' },
                    { icon: Lightbulb, label: 'INSIGHTS' },
                    { icon: ListOrdered, label: 'Orders' },
                    { icon: LayoutDashboard, label: 'Portfolio' },
                ].map((item) => (
                    <button
                        key={item.label}
                        onClick={() => handleTabChange(item.label)}
                        className={`flex flex-col items-center gap-1 transition-all duration-300 ${activeTab === item.label ? 'text-indigo-400 scale-110' : 'text-slate-500 hover:text-slate-300'}`}
                    >
                        <item.icon className={`w-5 h-5 ${activeTab === item.label ? 'drop-shadow-[0_0_8px_rgba(99,102,241,0.5)]' : ''}`} />
                        <span className="text-[8px] font-black uppercase tracking-tighter transition-opacity">{activeTab === item.label ? item.label.split(' ')[0] : ''}</span>
                    </button>
                ))}
                <button
                    onClick={() => setIsDrawerOpen(true)}
                    className="flex flex-col items-center gap-1 text-slate-500 hover:text-indigo-400 transition-all active:scale-90"
                >
                    <Menu className="w-5 h-5" />
                    <span className="text-[8px] font-black uppercase tracking-tighter">MENU</span>
                </button>
            </nav>

            {/* Mobile Slide-out Drawer */}
            <AnimatePresence>
                {isDrawerOpen && (
                    <div className="fixed inset-0 z-[200] lg:hidden">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsDrawerOpen(false)}
                            className="absolute inset-0 bg-black/60 backdrop-blur-md"
                        />
                        <motion.div
                            initial={{ x: '-100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '-100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="relative w-72 h-full glass-panel border-r border-white/10 flex flex-col p-6 shadow-2xl bg-[#0c0d12]/90"
                        >
                            <div className="flex items-center justify-between mb-8">
                                <h1 className="text-xl font-black tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent italic">
                                    TRADEVERSE
                                </h1>
                                <button
                                    onClick={() => setIsDrawerOpen(false)}
                                    className="p-2 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <nav className="flex-1 space-y-1 overflow-y-auto custom-scrollbar pr-2">
                                {navItems.map((item) => (
                                    <SidebarItem
                                        key={item.label}
                                        icon={item.icon}
                                        label={item.label}
                                        active={activeTab === item.label}
                                        onClick={() => handleTabChange(item.label)}
                                    />
                                ))}

                                <div className="mt-8 pt-6 border-t border-white/5">
                                    <button
                                        onClick={() => {
                                            setIsDrawerOpen(false);
                                            handleLogout();
                                        }}
                                        className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-red-500 hover:bg-red-500/10 transition-all font-bold uppercase text-xs tracking-widest"
                                    >
                                        <LogOut className="w-5 h-5" />
                                        Disconnect
                                    </button>
                                </div>
                            </nav>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
            {/* Sidebar Pane */}
            <aside className="w-44 glass-panel border-r border-white/10 flex flex-col p-2 hidden lg:flex shadow-[20px_0_50px_rgba(0,0,0,0.3)]">
                <div className="mb-4">
                    <div className="flex items-center justify-between">
                        <h1 className="text-xl font-black tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent italic px-2">
                            TRADEVERSE
                        </h1>
                    </div>
                </div>

                <div className="flex items-center gap-2 mt-1 px-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${marketStatus.isOpen ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-amber-500 shadow-[0_0_5px_#f59e0b]'}`} />
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">
                        {marketStatus.isOpen ? 'TERMINAL ACTIVE' : marketStatus.isHoliday ? 'MARKET HOLIDAY' : 'MARKET CLOSED'}
                    </p>
                </div>

                {/* Health Status Panel */}
                <div className="mb-2 space-y-1.5 px-2 py-2 rounded-lg bg-white/5 border border-white/5">
                    <div className="flex items-center justify-between">
                        <span className="text-[8px] uppercase font-bold text-slate-500 tracking-wider">Health</span>
                    </div>

                    {/* Backend Status */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Activity className="w-3 h-3 text-slate-400" />
                            <span className="text-xs font-medium text-slate-300">Backend</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${systemStatus.backend ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]' : 'bg-red-500'}`} />
                            <span className={`text-[10px] font-bold ${systemStatus.backend ? 'text-emerald-500' : 'text-red-500'}`}>
                                {systemStatus.backend ? 'ONLINE' : 'OFFLINE'}
                            </span>
                        </div>
                    </div>

                    {/* Broker Status */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Briefcase className="w-3 h-3 text-slate-400" />
                            <span className="text-xs font-medium text-slate-300">Broker</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${settings.angel_connected && settings.env === 'LIVE' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-amber-500 shadow-[0_0_8px_#f59e0b]'}`} />
                            <span className={`text-[10px] font-bold ${settings.angel_connected && settings.env === 'LIVE' ? 'text-emerald-500' : 'text-amber-500'}`}>
                                {settings.angel_connected && settings.env === 'LIVE' ? 'LIVE' : 'MOCK'}
                            </span>
                        </div>
                    </div>

                    {/* AI / Intelligence Status */}
                    <div className="flex items-center justify-between cursor-pointer group" onClick={() => { setActiveTab('Live Terminal'); setTerminalMode('SWARM'); }}>
                        <div className="flex items-center gap-2">
                            <Zap className="w-3 h-3 text-slate-400 group-hover:text-indigo-400 transition-colors" />
                            <span className="text-xs font-medium text-slate-300 group-hover:text-white transition-colors">Intelligence</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${systemStatus.intelligence ? 'bg-indigo-500 shadow-[0_0_8px_#6366f1]' : 'bg-slate-500'}`} />
                            <span className={`text-[10px] font-bold ${systemStatus.intelligence ? 'text-indigo-500' : 'text-slate-500'}`}>
                                {systemStatus.intelligence ? 'ACTIVE' : 'OFFLINE'}
                            </span>
                        </div>
                    </div>
                </div>

                <nav className="flex-1 space-y-1 overflow-y-auto custom-scrollbar pr-2 pb-20">
                    {navItems.map((item) => (
                        <SidebarItem
                            key={item.label}
                            icon={item.icon}
                            label={item.label}
                            active={activeTab === item.label}
                            onClick={() => handleTabChange(item.label)}
                        />
                    ))}

                    {/* Logout Button in Sidebar */}
                    <div className="mt-8 pt-6 border-t border-white/5 relative z-20">
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-red-500 hover:bg-red-500/10 hover:shadow-[0_0_15px_rgba(239,68,68,0.1)] transition-all group cursor-pointer hover:scale-105 active:scale-95"
                        >
                            <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
                            <span className="text-xs font-bold uppercase tracking-widest">Disconnect</span>
                        </button>
                    </div>
                </nav>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto custom-scrollbar pb-8 lg:pb-2">
                <div className="p-1.5 md:p-2 space-y-1">
                    {/* Top Bar */}
                    {/* Top Bar - Floating HUD */}
                    <header className="flex flex-row flex-nowrap justify-between items-center gap-2 sticky top-0 z-50 py-1 -mx-2 px-2 bg-[#0c0d12]/80 lg:bg-transparent backdrop-blur-lg lg:backdrop-blur-none transition-all overflow-x-auto no-scrollbar">
                        <div className="glass-premium px-3 py-1.5 rounded-full border border-white/15 shadow-2xl flex items-center gap-2 backdrop-blur-xl shrink-0">
                            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest group relative">
                                <input
                                    type="text"
                                    value={searchInput}
                                    onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            if (searchResults.length > 0) {
                                                selectSymbol(searchResults[0].symbol);
                                            } else {
                                                setSymbol(searchInput);
                                                setChartData([]);
                                            }
                                            setShowResults(false);
                                        }
                                    }}
                                    onFocus={() => {
                                        setSearchInput('');
                                        if (searchResults.length > 0) setShowResults(true);
                                    }}
                                    onBlur={() => {
                                        setTimeout(() => {
                                            if (!searchInput) setSearchInput(symbol);
                                            setShowResults(false);
                                        }, 200);
                                    }}
                                    placeholder="SEARCH..."
                                    className="bg-transparent border-none outline-none text-white font-black w-16 lg:w-22 focus:ring-0 placeholder:text-slate-700 text-[10px] lg:text-xs"
                                />
                                <Search className="w-3 h-3 text-slate-600 group-focus-within:text-indigo-400 transition-colors" />

                                {showResults && searchResults.length > 0 && (
                                    <div className="absolute top-full left-0 mt-2 w-64 bg-black/90 border border-white/10 rounded-xl backdrop-blur-xl shadow-2xl z-50 overflow-hidden">
                                        {searchResults.map((res) => (
                                            <div
                                                key={res.token}
                                                onClick={() => selectSymbol(res.symbol)}
                                                className="px-4 py-3 hover:bg-white/10 cursor-pointer border-b border-white/5 last:border-0"
                                            >
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm font-bold text-white">{res.symbol}</span>
                                                    <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">{res.exchange}</span>
                                                </div>
                                                <div className="text-[10px] text-slate-500 font-mono mt-0.5">{res.name}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-nowrap items-center gap-2 lg:gap-3 shrink-0 ml-auto">
                            {/* Unified Tactical HUD Group */}
                            <ControlToggle
                                label={isAutoMode ? "AUTO" : "MANUAL"}
                                active={isAutoMode}
                                onClick={handleModeToggle}
                                color="emerald"
                            />

                            <button
                                onClick={handleEmergencyStop}
                                className="px-2 py-1 h-[32px] rounded-lg border border-red-500/20 bg-red-500/5 hover:bg-red-500/20 transition-all flex items-center gap-1.5 hover:scale-105 active:scale-95 cursor-pointer z-50 group shrink-0"
                                title="KILL SWITCH"
                            >
                                <AlertTriangle className="w-2.5 h-2.5 text-red-500/60 group-hover:text-red-500" />
                                <span className="hidden xl:block text-[8px] font-black uppercase tracking-widest text-red-500/60 group-hover:text-red-500">KILL</span>
                            </button>

                            <MarketClock isOpen={marketStatus.isOpen} />

                            <StatusBadge
                                label="SYSTEM"
                                status={riskStatus.circuit_breaker_status === 'NOMINAL' ? 'NOMINAL' : 'HALTED'}
                                color={riskStatus.circuit_breaker_status === 'NOMINAL' ? 'emerald' : 'red'}
                                pulse={riskStatus.circuit_breaker_status !== 'NOMINAL'}
                            />

                            <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg border border-white/10 h-[38px] shrink-0">
                                <div className={`w-6 h-6 rounded-full flex items-center justify-center font-black text-[9px] border ${user.status === 'ONLINE' ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-slate-700/50 text-slate-400 border-white/5'}`}>
                                    {user.initials}
                                </div>
                                <span className={`hidden md:block text-[10px] font-black uppercase tracking-wider ${user.status === 'ONLINE' ? 'text-indigo-400' : 'text-slate-500'}`}>
                                    {user.name}
                                </span>
                            </div>

                            {settings.angel_connected && (
                                <StatusBadge
                                    label="BROKER"
                                    status="CONNECTED"
                                    color="emerald"
                                    pulse={true}
                                />
                            )}

                            <StatusBadge
                                label="REGIME"
                                status={data.regime}
                                color={data.regime === 'NOMINAL' ? 'emerald' : data.regime === 'VOLATILE' ? 'amber' : 'red'}
                            />
                        </div>
                    </header>

                    {activeTab === 'Live Terminal' && dailyBias && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.98, y: -10 }}
                            animate={{
                                opacity: 1, scale: 1, y: 0,
                                boxShadow: [`0 0 15px ${dailyBias.bias === 'BULLISH' ? 'rgba(16,185,129,0.15)' : dailyBias.bias === 'BEARISH' ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)'}`, `0 0 25px ${dailyBias.bias === 'BULLISH' ? 'rgba(16,185,129,0.3)' : dailyBias.bias === 'BEARISH' ? 'rgba(239,68,68,0.3)' : 'rgba(99,102,241,0.3)'}`],
                            }}
                            transition={{ duration: 3, repeat: Infinity, repeatType: 'reverse' }}
                            className={`p-3 rounded-xl bg-gradient-to-r ${dailyBias.bias === 'BULLISH' ? 'from-emerald-900/40 to-black/60 border-emerald-500/50' : dailyBias.bias === 'BEARISH' ? 'from-red-900/40 to-black/60 border-red-500/50' : 'from-indigo-900/40 to-black/60 border-indigo-500/50'} border backdrop-blur-xl mb-3 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative overflow-hidden`}
                        >
                            {/* Decorative Background Glow */}
                            <div className={`absolute top-0 right-0 w-32 h-32 blur-3xl rounded-full opacity-20 pointer-events-none ${dailyBias.bias === 'BULLISH' ? 'bg-emerald-500' : dailyBias.bias === 'BEARISH' ? 'bg-red-500' : 'bg-indigo-500'}`} />

                            <div className="flex flex-col gap-1 z-10 w-full md:w-auto flex-1">
                                <div className="flex items-center gap-2">
                                    <div className={`px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest ${dailyBias.bias === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-400' : dailyBias.bias === 'BEARISH' ? 'bg-red-500/20 text-red-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                                        DAILY STRATEGIST RECOMMENDATION: {dailyBias.bias}
                                    </div>
                                    <span className="text-[10px] text-white/40 font-mono flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {dailyBias.timestamp ? new Date(dailyBias.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'CALIBRATING'}
                                    </span>
                                </div>
                                <p className="text-sm font-bold text-white tracking-wide leading-relaxed mt-1">{dailyBias.recommendation}</p>
                            </div>

                            <div className="flex items-center gap-4 shrink-0 border-t md:border-t-0 md:border-l border-white/10 pt-3 md:pt-0 md:pl-4 z-10 w-full md:w-auto justify-between md:justify-end">
                                <div className="flex flex-col items-start md:items-end">
                                    <span className="text-[9px] text-slate-400 font-black uppercase tracking-widest mb-0.5">Confidence</span>
                                    <span className={`text-xl font-black tabular-nums ${dailyBias.bias === 'BULLISH' ? 'text-emerald-400' : dailyBias.bias === 'BEARISH' ? 'text-red-400' : 'text-indigo-400'}`}>{dailyBias.confidence}%</span>
                                </div>
                                <button onClick={fetchDailyBias} className="p-2 hover:bg-white/10 rounded-lg text-white/50 hover:text-white transition-all bg-black/20 border border-white/5 group">
                                    <RefreshCw className={`w-4 h-4 group-hover:rotate-180 transition-transform duration-500 ${isBiasLoading ? 'animate-spin' : ''}`} />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {activeTab === 'Live Terminal' ? (
                        <div className="space-y-2 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            {/* Inner Tab Toggle */}
                            <div className="flex items-center gap-2 mb-2">
                                <button
                                    onClick={() => setTerminalMode('TACTICAL')}
                                    className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all border ${terminalMode === 'TACTICAL'
                                        ? 'bg-indigo-500 text-white border-indigo-500 shadow-lg shadow-indigo-500/20'
                                        : 'bg-white/5 text-slate-500 border-white/10 hover:bg-white/10'
                                        }`}
                                >
                                    Tactical HUD
                                </button>
                                <button
                                    onClick={() => setTerminalMode('SWARM')}
                                    className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all border ${terminalMode === 'SWARM'
                                        ? 'bg-purple-500 text-white border-purple-500 shadow-lg shadow-purple-500/20'
                                        : 'bg-white/5 text-slate-500 border-white/10 hover:bg-white/10'
                                        }`}
                                >
                                    AI Swarm Intelligence
                                </button>
                            </div>

                            {terminalMode === 'TACTICAL' ? (
                                <div className="grid grid-cols-1 lg:grid-cols-4 gap-2">
                            {/* Command Center: Execution + System Stats */}
                            {/* Command Center: Execution Protocol */}
                            <div className="lg:col-span-1 flex flex-col">
                                <HUDCard title="EXECUTION PROTOCOL" neonColor="indigo" className="flex-1">
                                    <TradeChecklist symbol={symbol} analysis={data} />
                                </HUDCard>
                            </div>

                            <div className="lg:col-span-3">
                                <HUDCard
                                    title="TACTICAL COMMAND CENTER"
                                    neonColor="indigo"
                                    className="relative"
                                    action={
                                        <button onClick={runSystemScan} disabled={isScanning} className="flex items-center gap-1 px-1.5 py-0.5 bg-white/5 hover:bg-white/10 rounded border border-white/10 text-[6px] font-black tracking-widest uppercase transition-all">
                                            {isScanning ? <RefreshCw className="w-2 h-2 animate-spin" /> : <Activity className="w-2 h-2" />}
                                            SCAN
                                        </button>
                                    }
                                >
                                    <div className="pt-3 p-1.5 flex flex-col md:flex-row items-center gap-1.5 relative z-20">
                                        {/* Status Indicators Group */}
                                        <div className="flex gap-1.5 shrink-0">
                                            <div className="bg-white/[0.02] p-1 rounded-lg border border-white/10 flex flex-col justify-between w-[70px] h-[45px]">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[5px] font-black text-slate-500 uppercase tracking-widest">Health</span>
                                                    <Shield className={`w-2 h-2 ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'text-emerald-500' : 'text-red-500 animate-pulse'}`} />
                                                </div>
                                                <div className={`text-[10px] font-black tracking-tighter ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'text-emerald-400' : 'text-red-400'}`}>
                                                    STABLE
                                                </div>
                                            </div>

                                            <div className="bg-white/[0.02] p-1 rounded-lg border border-white/10 flex flex-col justify-between w-[70px] h-[45px]">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[5px] font-black text-slate-500 uppercase tracking-widest">Regime</span>
                                                    <Globe className="w-2 h-2 text-indigo-400" />
                                                </div>
                                                <div className="text-[10px] font-black tracking-tighter text-emerald-400 truncate">
                                                    {data.regime}
                                                </div>
                                            </div>

                                            <div className="bg-white/[0.02] p-1 rounded-lg border border-white/10 flex flex-col justify-between w-[90px] h-[45px]">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[5px] font-black text-slate-500 uppercase tracking-widest">Risk</span>
                                                    <span className="text-[6px] font-black text-white">₹{riskStatus.current_daily_loss?.toFixed(0)}</span>
                                                </div>
                                                <div className="h-0.5 w-full bg-white/10 rounded-full mt-0.5">
                                                    <div className="h-full bg-red-500" style={{ width: `${Math.min(((riskStatus.current_daily_loss || 0) / (riskStatus.daily_loss_limit || 1)) * 100, 100)}%` }} />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Committee Hub: High Visibility */}
                                        <div className="flex-1 w-full bg-indigo-500/5 p-3 rounded-xl border border-indigo-500/20 flex flex-col justify-center min-w-[280px]">
                                            <div className="flex items-center justify-between mb-2 px-1">
                                                <div className="flex items-center gap-1.5">
                                                    <Zap className="w-3 h-3 text-indigo-400" />
                                                    <span className="text-[8px] font-black text-indigo-300 uppercase tracking-[0.1em]">Consensus Hub</span>
                                                </div>
                                                <span className="text-[9px] font-mono text-indigo-400 italic font-bold">Quorum: {data.regime === 'NOMINAL' ? '3/5' : '5/5'}</span>
                                            </div>
                                            <div className="flex gap-4 overflow-x-auto pb-1 custom-scrollbar items-center">
                                                <AgentStatus label="TECH" status={getAgentStatus('TECH')} icon={TrendingUp} colorClass="text-emerald-400" />
                                                <AgentStatus label="TFT" status={getAgentStatus('TFT')} icon={Activity} colorClass="text-purple-400" />
                                                <AgentStatus label="RL" status={getAgentStatus('RL')} icon={Zap} colorClass="text-amber-400" />
                                                <AgentStatus label="SENT" status={getAgentStatus('SENT')} icon={Brain} colorClass="text-blue-400" />
                                                <AgentStatus label="OPT" status={getAgentStatus('OPT')} icon={ListOrdered} colorClass="text-indigo-400" />
                                            </div>
                                        </div>
                                    </div>
                                </HUDCard>

                                {/* High-Density Intelligence Row: Nexus Stack */}
                                <div className="grid grid-cols-1 lg:grid-cols-4 gap-1 mt-1">
                                    <div className="lg:col-span-3 flex flex-col gap-1 h-full">
                                        <HUDCard title="SWARM REPORTS" neonColor="purple" className="flex-1 min-h-[60px]" lastUpdated={lastAnalysisUpdate}>
                                            <div className="p-1 grid grid-cols-2 md:grid-cols-3 gap-1 overflow-y-auto custom-scrollbar h-full">
                                                <AnimatePresence mode="wait">
                                                    {analysis && analysis.sentiment_analysis ? (
                                                        [
                                                            { role: "Sentiment", text: analysis.sentiment_analysis, icon: Brain, color: "text-blue-400 bg-blue-500/5" },
                                                            { role: "Technical", text: analysis.technical_analysis || "Processing...", icon: TrendingUp, color: "text-emerald-400 bg-emerald-500/5" },
                                                            { role: "Options", text: `PCR: ${analysis.pcr?.toFixed(2)}`, icon: ListOrdered, color: "text-indigo-400 bg-indigo-500/5" },
                                                            { role: "TFT", text: `Pred: ${analysis.tft_prediction || 'UP'}`, icon: Activity, color: "text-purple-400 bg-purple-500/5" },
                                                            { role: "RL Sniper", text: `Action: ${analysis.rl_action || 0}`, icon: Zap, color: "text-amber-400 bg-amber-500/5" },
                                                        ].map((report, idx) => (
                                                            <div key={idx} className={`px-1.5 py-0.5 rounded border border-white/5 flex items-center gap-1.5 ${report.color}`}>
                                                                <span className="text-[7px] font-black uppercase tracking-tighter opacity-70 truncate min-w-[40px]">{report.role}:</span>
                                                                <p className="text-[7px] text-slate-300 font-mono truncate">{report.text}</p>
                                                            </div>
                                                        ))
                                                    ) : <div className="col-span-3 h-8 flex items-center justify-center text-[7px] uppercase font-black tracking-widest text-slate-700">Calibrating...</div>}
                                                </AnimatePresence>
                                            </div>
                                        </HUDCard>

                                        <HUDCard title="SENSITIVITY" neonColor="amber" className="flex-1 min-h-[60px] relative" lastUpdated={lastAnalysisUpdate}>
                                            <GreeksCheatSheet data={data} compact={true} />
                                        </HUDCard>
                                    </div>

                                    <div className="lg:col-span-1">
                                        <HUDCard title="CORTEX" neonColor="purple" className="h-full relative min-h-[125px]" lastUpdated={lastAnalysisUpdate}>
                                            <div className="p-1 h-full flex flex-col transition-all">
                                                <div className="bg-black/40 p-1 rounded-lg border border-white/5 flex items-center justify-between">
                                                    <div className={`text-lg font-black tabular-nums ${data.signal === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                                                        {data.confidence}%
                                                    </div>
                                                    <div className="scale-75">
                                                        <ConfidenceGauge score={data.confidence || 0} size="sm" />
                                                    </div>
                                                </div>
                                                <div className="flex-1 bg-black/60 p-1 border border-indigo-500/10 rounded-lg overflow-hidden flex flex-col mt-1">
                                                    <div className="text-[7px] font-mono leading-none overflow-y-auto custom-scrollbar flex-1 space-y-0.5">
                                                        {terminalLogs.slice(-4).map((log, i) => (
                                                            <div key={i} className="truncate text-emerald-500/60">
                                                                {">"} {log.message}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                                <button onClick={runAgentAnalysis} disabled={isAnalyzing} className="w-full py-1 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 text-[7px] font-black uppercase tracking-widest border border-indigo-500/20 rounded mt-1">
                                                    {isAnalyzing ? "SYNC" : "INFER"}
                                                </button>
                                            </div>
                                        </HUDCard>
                                    </div>
                                </div>
                            </div>

                                </div>
                            ) : (
                                <div className="space-y-4 animate-in fade-in zoom-in duration-500 pb-20">
                                    {/* Brain Visualizer - Hero Section */}
                                    <div className="w-full">
                                        <BrainVisualizer scores={analysis?.model_scores || {}} className="border-purple-500/20 shadow-xl shadow-purple-500/5" />
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                                        {/* Swarm Status Panel */}
                                        <div className="lg:col-span-1">
                                            <HUDCard title="NEURAL TRAINING" neonColor="purple" className="flex-1">
                                                <div className="p-4 space-y-6">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <div>
                                                            <h4 className="text-sm font-black text-white uppercase tracking-wider">Status</h4>
                                                            <p className="text-[10px] font-black text-purple-400 mt-1">{trainingStatus.stage}</p>
                                                        </div>
                                                        <button
                                                            onClick={() => setShowTrainingConfirm(true)}
                                                            disabled={isTraining}
                                                            className={`px-6 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${isTraining
                                                                ? 'bg-slate-500/20 text-slate-500 cursor-not-allowed'
                                                                : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-500/20'
                                                                }`}
                                                        >
                                                            {isTraining ? 'Training...' : 'Rebuild Swarm'}
                                                        </button>
                                                    </div>

                                                    {trainingStatus.progress > 0 && (
                                                        <div className="space-y-2">
                                                            <div className="flex items-center justify-between text-[10px]">
                                                                <span className="text-slate-400 italic">{trainingStatus.message}</span>
                                                                <span className="text-purple-400 font-black">{trainingStatus.progress}%</span>
                                                            </div>
                                                            <div className="w-full h-1.5 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                                                <div
                                                                    className="h-full bg-gradient-to-r from-purple-500 to-indigo-500"
                                                                    style={{ width: `${trainingStatus.progress}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="grid grid-cols-1 gap-2">
                                                        {[
                                                            { name: 'Daily Strategist', key: 'DAILY_STRATEGIST', icon: TrendingUp },
                                                            { name: 'Intraday Sniper', key: 'INTRADAY_SNIPER', icon: Zap },
                                                            { name: 'Temporal Context', key: 'TFT_TRANSFORMER', icon: Activity },
                                                            { name: 'RL Timing', key: 'RL_OPTIMIZER', icon: Brain },
                                                            { name: 'Regime Cluster', key: 'REGIME_ENGINE', icon: Shield }
                                                        ].map((stage) => {
                                                            const isComplete = (['DAILY_STRATEGIST', 'INTRADAY_SNIPER', 'TFT_TRANSFORMER', 'RL_OPTIMIZER', 'REGIME_ENGINE'].indexOf(stage.key) < ['DAILY_STRATEGIST', 'INTRADAY_SNIPER', 'TFT_TRANSFORMER', 'RL_OPTIMIZER', 'REGIME_ENGINE'].indexOf(trainingStatus?.stage || 'IDLE'));
                                                            const isActive = trainingStatus.stage === stage.key;
                                                            return (
                                                                <div key={stage.key} className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${isComplete ? 'bg-emerald-500/5 border-emerald-500/20 opacity-100' : isActive ? 'bg-purple-500/10 border-purple-500/40 animate-pulse' : 'bg-black/20 border-white/5 opacity-40'}`}>
                                                                    <stage.icon className={`w-4 h-4 ${isComplete ? 'text-emerald-400' : isActive ? 'text-purple-400' : 'text-slate-600'}`} />
                                                                    <span className={`text-[10px] font-black uppercase tracking-widest ${isComplete ? 'text-emerald-400' : isActive ? 'text-purple-400' : 'text-slate-600'}`}>{stage.name}</span>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            </HUDCard>
                                        </div>

                                        {/* Swarm Metrics Panel */}
                                        <div className="lg:col-span-2">
                                            <HUDCard title="SWARM VALIDATION METRICS" neonColor="indigo" className="h-full">
                                                {!modelMetrics ? (
                                                    <div className="h-full flex flex-col items-center justify-center py-20 opacity-20">
                                                        <Database className="w-12 h-12 mb-4" />
                                                        <p className="text-[10px] font-black uppercase tracking-widest">Awaiting Validation Pulse...</p>
                                                    </div>
                                                ) : (
                                                    <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                                                        {['daily', 'intraday'].map((type) => {
                                                            const m = modelMetrics[type];
                                                            if (!m) return null;
                                                            return (
                                                                <div key={type} className="bg-white/5 border border-white/10 rounded-2xl p-4 hover:border-indigo-500/30 transition-all group">
                                                                    <div className="flex items-center justify-between mb-4">
                                                                        <h4 className="text-xs font-black text-white uppercase tracking-widest">{type} ENSEMBLE</h4>
                                                                        <span className="text-sm font-black text-emerald-400 font-mono">+{m.final_strategy_return}%</span>
                                                                    </div>
                                                                    <div className="grid grid-cols-3 gap-2">
                                                                        <div className="text-center">
                                                                            <p className="text-[8px] font-black text-slate-500 uppercase mb-1">Prec</p>
                                                                            <p className="text-xs font-black text-indigo-400">{(m.precision * 100).toFixed(1)}%</p>
                                                                        </div>
                                                                        <div className="text-center">
                                                                            <p className="text-[8px] font-black text-slate-500 uppercase mb-1">F1</p>
                                                                            <p className="text-xs font-black text-emerald-400">{(m.f1 || 0).toFixed(2)}</p>
                                                                        </div>
                                                                        <div className="text-center">
                                                                            <p className="text-[8px] font-black text-slate-500 uppercase mb-1">Trades</p>
                                                                            <p className="text-xs font-black text-white">{m.trade_count}</p>
                                                                        </div>
                                                                    </div>
                                                                    <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center">
                                                                        <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Accuracy</span>
                                                                        <div className="flex-1 mx-4 h-1 bg-white/5 rounded-full overflow-hidden">
                                                                            <div className="h-full bg-indigo-500" style={{ width: `${m.accuracy * 100}%` }} />
                                                                        </div>
                                                                        <span className="text-[10px] font-black text-slate-400 font-mono">{(m.accuracy * 100).toFixed(0)}%</span>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                )}
                                            </HUDCard>
                                        </div>
                                    </div>
                                    
                                    {/* Swarm Monologue / Full Terminal Section */}
                                    <HUDCard title="LIVE SWARM INTELLIGENCE LOGS" neonColor="emerald" className="min-h-[300px]">
                                        <div className="p-4 font-mono text-[11px] leading-relaxed overflow-y-auto max-h-[400px] custom-scrollbar bg-black/40 rounded-xl border border-white/5">
                                            {terminalLogs.length === 0 ? (
                                                <p className="text-slate-700 italic">Listening for neural consensus events...</p>
                                            ) : (
                                                terminalLogs.map((log, i) => (
                                                    <div key={i} className="mb-2 flex gap-4 animate-in fade-in slide-in-from-left-2 transition-all">
                                                        <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                                                        <span className={`${log.type === 'ai' ? 'text-purple-400' : log.type === 'error' ? 'text-red-400' : log.type === 'signal' ? 'text-emerald-400 font-bold' : 'text-slate-400'}`}>
                                                            {log.type === 'ai' ? '🧠' : log.type === 'signal' ? '🎯' : '⚛️'} {log.message}
                                                        </span>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </HUDCard>
                                </div>
                            )}

                        </div>
                    ) : (activeTab || "").toLowerCase() === 'settings' ? (
                        <div className="h-full flex gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            {/* Left Column: Sidebar & Environment */}
                            <div className="w-80 flex flex-col gap-6">
                                {/* Settings Navigation */}
                                <div className="glass-panel p-4 rounded-[32px] space-y-2">
                                    {[
                                        { id: 'API Keys', icon: Key, label: 'API Keys', desc: 'Manage Credentials' },
                                        { id: 'Intelligence', icon: Brain, label: 'Intelligence', desc: 'AI Training' },
                                        { id: 'Notifications', icon: Bell, label: 'Notifications', desc: 'Alert Configuration' },
                                        { id: 'Appearance', icon: Eye, label: 'Appearance', desc: 'Theme & Layout' },
                                        { id: 'System', icon: Cpu, label: 'System', desc: 'Logs & Diagnostics' },
                                    ].map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => setActiveSettingsTab(item.id)}
                                            className={`w-full flex items-center gap-4 p-4 rounded-2xl transition-all duration-300 text-left group ${activeSettingsTab === item.id
                                                ? 'bg-indigo-500/10 border border-indigo-500/20'
                                                : 'hover:bg-white/5 border border-transparent'
                                                }`}
                                        >
                                            <div className={`p-2 rounded-xl ${activeSettingsTab === item.id ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-white/5 text-slate-500 group-hover:text-indigo-400'}`}>
                                                <item.icon className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h4 className={`text-sm font-black tracking-tight ${activeSettingsTab === item.id ? 'text-white' : 'text-slate-400 group-hover:text-white'}`}>{item.label}</h4>
                                                <p className="text-[10px] uppercase font-bold text-slate-600 tracking-wider group-hover:text-slate-500">{item.desc}</p>
                                            </div>
                                        </button>
                                    ))}
                                </div>

                                {/* Environment Control Card */}
                                <HUDCard title="ENVIRONMENT" neonColor="emerald" className="p-6 mt-auto">
                                    <div className="absolute top-0 right-0 p-4 opacity-10">
                                        <Globe className="w-24 h-24 text-emerald-500 rotate-12" />
                                    </div>
                                    <h4 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-400 mb-6 flex items-center gap-2 neon-text-emerald">
                                        <Zap className="w-4 h-4" /> System Environment
                                    </h4>

                                    <div className="bg-black/40 p-1.5 rounded-xl flex relative mb-6 border border-emerald-500/20 shadow-inner">
                                        <div className={`absolute inset-y-1.5 w-1/2 bg-emerald-500/20 rounded-lg transition-all duration-300 border border-emerald-500/30 ${settings.env === 'LIVE' ? 'left-[4px]' : 'left-[50%]'}`} />
                                        <button
                                            onClick={() => handleEnvSwitch('LIVE')}
                                            className={`relative flex-1 py-3 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all z-10 
                                                ${settings.env === 'LIVE' ? 'text-white' : 'text-slate-500 hover:text-slate-300'}
                                                ${!settings.angel_connected ? 'opacity-80' : ''}
                                            `}
                                        >
                                            <div className="flex items-center justify-center gap-1">
                                                {!settings.angel_connected && <Lock className="w-3 h-3" />}
                                                Live
                                            </div>
                                        </button>
                                        <button
                                            onClick={() => handleEnvSwitch('MOCK')}
                                            className={`relative flex-1 py-3 px-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all z-10 ${settings.env === 'MOCK' ? 'text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]' : 'text-slate-500'}`}
                                        >
                                            Mock
                                        </button>
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex justify-between items-center bg-black/20 px-4 py-3 rounded-lg border border-white/5">
                                            <span className="text-[10px] font-black uppercase text-slate-500">API Link</span>
                                            <span className={`text-[10px] font-black uppercase px-2 py-1 rounded border ${settings.angel_connected
                                                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                                                : 'text-red-400 bg-red-500/10 border-red-500/20'}`}>
                                                {settings.angel_connected ? 'Connected' : 'Missing'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center bg-black/20 px-4 py-3 rounded-lg border border-white/5">
                                            <span className="text-[10px] font-black uppercase text-slate-500">Session</span>
                                            <span className={`text-[10px] font-black uppercase px-2 py-1 rounded border ${settings.angel_connected
                                                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                                                : 'text-slate-500 bg-slate-500/10 border-slate-500/20'}`}>
                                                {settings.angel_connected ? 'Active' : 'Offline'}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center bg-black/20 px-4 py-3 rounded-lg border border-white/5">
                                            <span className="text-[10px] font-black uppercase text-slate-500">Ping</span>
                                            <span className="text-[10px] font-black uppercase text-amber-400"><ScrambleText text="988ms" /></span>
                                        </div>
                                    </div>
                                </HUDCard>
                            </div>

                            {/* Right Column: Content Area */}
                            <div className="flex-1 glass-panel p-10 rounded-[40px] relative overflow-hidden">
                                {activeSettingsTab === 'API Keys' ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                                        <div className="flex items-start gap-6 mb-8">
                                            <div className="p-4 bg-indigo-500/10 rounded-3xl text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/10">
                                                <Key className="w-8 h-8" />
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-black text-white tracking-tight">API Credentials</h3>
                                                <p className="text-slate-500 text-sm font-medium mt-2 max-w-md">Securely manage your broker credentials. Keys are encrypted at rest.</p>
                                            </div>
                                        </div>
                                        <div className="space-y-6 pt-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Client ID</label>
                                                    <input
                                                        type="text"
                                                        id="angel_client_id"
                                                        name="angel_client_id"
                                                        autocomplete="username"
                                                        value={credentials.angel_client_id}
                                                        onChange={(e) => setCredentials({ ...credentials, angel_client_id: e.target.value })}
                                                        placeholder="Client ID"
                                                        className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-indigo-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Password / MPIN</label>
                                                    <input
                                                        type="password"
                                                        id="angel_password"
                                                        name="angel_password"
                                                        autocomplete="current-password"
                                                        value={credentials.angel_password}
                                                        onChange={(e) => setCredentials({ ...credentials, angel_password: e.target.value })}
                                                        placeholder="Password"
                                                        className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-indigo-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                    />
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Angel API Key</label>
                                                <input
                                                    type="text"
                                                    id="angel_api_key"
                                                    name="angel_api_key"
                                                    autocomplete="off"
                                                    value={credentials.angel_api_key}
                                                    onChange={(e) => setCredentials({ ...credentials, angel_api_key: e.target.value })}
                                                    placeholder="SmartAPI Key"
                                                    className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-indigo-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">TOTP Secret Key</label>
                                                <input
                                                    type="password"
                                                    id="angel_totp_key"
                                                    name="angel_totp_key"
                                                    autocomplete="off"
                                                    value={credentials.angel_totp_key}
                                                    onChange={(e) => setCredentials({ ...credentials, angel_totp_key: e.target.value })}
                                                    placeholder="TOTP Secret (for 2FA)"
                                                    className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-indigo-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                />
                                            </div>

                                            {/* Advanced Diagnostics Section */}
                                            <div className="p-4 bg-white/5 border border-white/10 rounded-2xl space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] font-black uppercase text-slate-500 tracking-wider">Server Health</span>
                                                    <span className={`text-[10px] font-mono font-bold ${serverLatency?.includes('ONLINE') ? 'text-emerald-400' : serverLatency?.includes('Error') || serverLatency === 'UNREACHABLE' ? 'text-red-400' : 'text-slate-400'}`}>
                                                        {serverLatency || 'NOT CHECKED'}
                                                    </span>
                                                </div>
                                                <button
                                                    onClick={checkServerHealth}
                                                    className="w-full py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-300 transition-all flex items-center justify-center gap-2"
                                                >
                                                    <Zap className="w-3 h-3" /> Check Server Status
                                                </button>
                                            </div>

                                            <div className="pt-4 flex flex-col gap-3">
                                                <div className="flex gap-3">
                                                    <button
                                                        onClick={handleUpdateCredentials}
                                                        disabled={isConnecting}
                                                        className={`flex-1 py-4 ${isConnecting ? 'bg-indigo-500/50 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500'} text-white rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-3 active:scale-95`}
                                                    >
                                                        {isConnecting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                                                        {isConnecting ? `Connecting (${connCountdown}s)...` : 'Connect Angel One'}
                                                    </button>

                                                    {isConnecting && (
                                                        <button
                                                            onClick={() => abortControllerRef.current?.abort()}
                                                            className="px-6 py-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-2xl text-xs font-black uppercase tracking-widest transition-all active:scale-95"
                                                            title="Cancel Connection"
                                                        >
                                                            Cancel
                                                        </button>
                                                    )}
                                                </div>


                                                {settings.angel_connected && (
                                                    <button
                                                        onClick={() => setShowDisconnectConfirm(true)}
                                                        className="w-full py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-lg flex items-center justify-center gap-2"
                                                    >
                                                        <LogOut className="w-4 h-4" /> Disconnect Angel One
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : activeSettingsTab === 'Intelligence' ? (
                                    <div className="h-full flex flex-col items-center justify-center py-20 animate-in fade-in zoom-in">
                                        <div className="w-20 h-20 bg-purple-500/10 rounded-3xl flex items-center justify-center border border-purple-500/20 mb-6 shadow-lg shadow-purple-500/10">
                                            <Brain className="w-10 h-10 text-purple-400" />
                                        </div>
                                        <h3 className="text-xl font-black text-white uppercase tracking-widest mb-2">Relocated to Live Terminal</h3>
                                        <p className="text-slate-500 text-sm font-medium mb-8 max-w-sm text-center">We've moved the AI Swarm Intelligence controls directly into the Live Terminal tab for faster tactical access.</p>
                                        <button
                                            onClick={() => { setActiveTab('Live Terminal'); setTerminalMode('SWARM'); }}
                                            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95"
                                        >
                                            Go to AI Swarm
                                        </button>
                                    </div>
                                ) : activeSettingsTab === 'Notifications' ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500 overflow-y-auto max-h-[60vh] pr-4 custom-scrollbar">
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                            {/* WhatsApp Section */}
                                            <div className="space-y-6">
                                                <div className="flex items-start gap-4 mb-4">
                                                    <div className="p-3 bg-emerald-500/10 rounded-2xl text-emerald-400 border border-emerald-500/20">
                                                        <MessageCircle className="w-6 h-6" />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-lg font-black text-white tracking-tight">WhatsApp</h3>
                                                        <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mt-1">Via CallMeBot API</p>
                                                    </div>
                                                </div>

                                                <div className="space-y-4 pt-2">
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Phone Number</label>
                                                        <input
                                                            type="text"
                                                            value={credentials.whatsapp_phone}
                                                            onChange={(e) => setCredentials({ ...credentials, whatsapp_phone: e.target.value })}
                                                            placeholder="+9199********"
                                                            className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">API Key</label>
                                                        <input
                                                            type="password"
                                                            value={credentials.whatsapp_api_key}
                                                            onChange={(e) => setCredentials({ ...credentials, whatsapp_api_key: e.target.value })}
                                                            placeholder="CallMeBot API Key"
                                                            className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-emerald-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                        />
                                                    </div>
                                                    <div className="pt-4 flex gap-3">
                                                        <button
                                                            onClick={handleUpdateWhatsAppSettings}
                                                            className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95"
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            onClick={handleSendTestWhatsApp}
                                                            disabled={!credentials.whatsapp_phone || !credentials.whatsapp_api_key}
                                                            className="px-4 py-3 bg-white/5 hover:bg-white/10 text-emerald-400 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 disabled:opacity-30"
                                                        >
                                                            Test
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Telegram Section */}
                                            <div className="space-y-6">
                                                <div className="flex items-start gap-4 mb-4">
                                                    <div className="p-3 bg-sky-500/10 rounded-2xl text-sky-400 border border-sky-500/20">
                                                        <Send className="w-6 h-6" />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-lg font-black text-white tracking-tight">Telegram</h3>
                                                        <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mt-1">Via Bot API</p>
                                                    </div>
                                                </div>

                                                <div className="space-y-4 pt-2">
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Bot Token</label>
                                                        <input
                                                            type="password"
                                                            value={credentials.telegram_bot_token}
                                                            onChange={(e) => setCredentials({ ...credentials, telegram_bot_token: e.target.value })}
                                                            placeholder="123456789:ABCDEF..."
                                                            className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-sky-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Chat ID</label>
                                                        <input
                                                            type="text"
                                                            value={credentials.telegram_chat_id}
                                                            onChange={(e) => setCredentials({ ...credentials, telegram_chat_id: e.target.value })}
                                                            placeholder="e.g. 987654321"
                                                            className="w-full bg-black/20 border border-white/5 rounded-2xl px-6 py-4 text-sm font-mono text-slate-300 focus:outline-none focus:border-sky-500/50 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                        />
                                                    </div>
                                                    <div className="pt-4 flex gap-3">
                                                        <button
                                                            onClick={handleUpdateTelegramSettings}
                                                            className="flex-1 py-3 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95"
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            onClick={handleSendTestTelegram}
                                                            disabled={!credentials.telegram_bot_token || !credentials.telegram_chat_id}
                                                            className="px-4 py-3 bg-white/5 hover:bg-white/10 text-sky-400 border border-sky-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 disabled:opacity-30"
                                                        >
                                                            Test
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : activeSettingsTab === 'System' ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                                        <div className="flex items-start gap-6 mb-8">
                                            <div className="p-4 bg-emerald-500/10 rounded-3xl text-emerald-400 border border-emerald-500/20 shadow-lg shadow-emerald-500/10">
                                                <Cpu className="w-8 h-8" />
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-black text-white tracking-tight">System Configuration</h3>
                                                <p className="text-slate-500 text-sm font-medium mt-2 max-w-md">Manage advanced network settings and backend targeting.</p>
                                            </div>
                                        </div>
                                        <div className="space-y-6 pt-4">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black uppercase text-slate-500 tracking-wider ml-1">Custom Backend URL (Local Tunnel)</label>
                                                <input
                                                    type="url"
                                                    defaultValue={localStorage.getItem('tradeverse_api_url') || ''}
                                                    onChange={(e) => localStorage.setItem('tradeverse_api_url', e.target.value)}
                                                    placeholder="e.g., https://your-tunnel.ngrok-free.app (Leave empty for Default)"
                                                    className="w-full bg-black/20 border border-emerald-500/20 rounded-2xl px-6 py-4 text-sm font-mono text-emerald-300 focus:outline-none focus:border-emerald-500/60 focus:bg-black/40 transition-all placeholder:text-slate-700"
                                                />
                                                <p className="text-xs text-slate-500 mt-2 px-1">
                                                    Enter your ngrok or localtunnel URL here to bypass the main cloud backend. <br />
                                                    <span className="text-emerald-400 font-bold">Important:</span> Refresh the page after saving to reconnect.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center opacity-30">
                                        <Settings className="w-16 h-16 mb-4 animate-spin-slow" />
                                        <p className="text-xs font-black uppercase tracking-widest">Section {activeSettingsTab} Under Construction</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : activeTab.toLowerCase() === 'orders' ? (
                        <div className="space-y-6">
                            <div className="flex justify-end pr-2">
                                <button
                                    onClick={placeTestOrder}
                                    className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-indigo-500/20 flex items-center gap-2 active:scale-95 transition-all"
                                >
                                    <Zap className="w-4 h-4" /> Place Test Order
                                </button>
                            </div>
                            <Orders />
                        </div>
                    ) : activeTab.toLowerCase() === 'simulations' ? (
                        <PaperTrade token={token} symbol={symbol} ltp={data.price || 0} />
                    ) : activeTab.toLowerCase() === 'observatory' ? (
                        <Observatory token={token} />
                    ) : activeTab.toLowerCase() === 'option chain & gex' ? (
                        <OptionChainGEX symbol={symbol} />
                    ) : activeTab.toLowerCase() === 'strategies' ? (
                        <Strategies />
                    ) : activeTab.toLowerCase() === 'lessons learned' ? (
                        <LessonsLearned />
                    ) : activeTab.toLowerCase() === 'backtest' ? (
                        <Backtest />
                    ) : activeTab.toLowerCase() === 'analytics' ? (
                        <Analytics />
                    ) : activeTab.toLowerCase() === 'insights' ? (
                        <Insights />
                    ) : activeTab.toLowerCase() === 'smallcases' ? (
                        <Smallcases />
                    ) : activeTab.toLowerCase() === 'market pulse' ? (
                        <MarketPulse />
                    ) : activeTab.toLowerCase() === 'portfolio' ? (
                        <Portfolio />
                    ) : activeTab.toLowerCase() === 'system health' ? (
                        <SystemHealth />
                    ) : (
                        <div className="h-[70vh] flex flex-col items-center justify-center text-slate-600 space-y-4 animate-in fade-in zoom-in duration-500">
                            <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center border border-white/5">
                                <LayoutDashboard className="w-10 h-10 opacity-20" />
                            </div>
                            <p className="text-xs font-black uppercase tracking-[0.3em] opacity-30 italic">{activeTab} section under development</p>
                        </div>
                    )
                    }
                </div >
            </main >

            {/* Login Modal */}
            < AnimatePresence >
                {showLogin && (
                    <LoginModal
                        isOpen={showLogin}
                        onClose={() => setShowLogin(false)}
                        onLogin={(authToken) => {
                            setIsLoggedIn(true);
                            setToken(authToken); // Store valid token
                            localStorage.setItem('authToken', authToken); // Critical Fix: Persist token to localStorage
                            if (authToken === 'mock-token-123') setIsOwner(true);
                            setUser({ name: 'Pro Trader', initials: 'PT', status: 'ONLINE', broker: 'ANGEL ONE' });
                            playInitSound();
                        }}
                        onGuestLogin={handleGuestLogin}
                    />
                )}
            </AnimatePresence >

            {/* Emergency Kill Switch Modal */}
            < AnimatePresence >
                {showEmergencyConfirm && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => { setShowEmergencyConfirm(false); setEmergencyResult(null); }}
                            className="absolute inset-0 bg-red-950/40 backdrop-blur-md"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 10 }}
                            className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] shadow-2xl border-red-500/30 bg-black/80"
                        >
                            <div className="text-center space-y-4 mb-8">
                                <div className={`w-20 h-20 mx-auto mb-4 rounded-3xl flex items-center justify-center border shadow-2xl transition-all duration-500 ${emergencyResult?.success ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-emerald-500/10' :
                                    emergencyResult?.success === false ? 'bg-red-500/10 text-red-500 border-red-500/20 shadow-red-500/10' :
                                        'bg-red-500/10 text-red-500 border-red-500/20 shadow-red-500/20'
                                    } ${isLiquidating ? 'animate-spin' : ''}`}>
                                    {isLiquidating ? <RefreshCw className="w-10 h-10" /> :
                                        emergencyResult?.success ? <CheckCircle className="w-10 h-10" /> :
                                            <AlertTriangle className="w-10 h-10" />}
                                </div>
                                <h3 className={`text-3xl font-black tracking-tighter ${emergencyResult?.success ? 'text-emerald-400' : 'text-red-500'}`}>
                                    {isLiquidating ? 'EXECUTING...' :
                                        emergencyResult?.success ? 'PROTOCOL SUCCESS' :
                                            emergencyResult?.success === false ? 'PROTOCOL FAILED' :
                                                'SYSTEM KILL SWITCH'}
                                </h3>
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] leading-relaxed">
                                    {isLiquidating
                                        ? 'Liquidating all market positions. Please wait.'
                                        : emergencyResult?.message
                                            ? emergencyResult.message
                                            : <>Are you sure you want to <span className="text-red-400">LIQUIDATE ALL POSITIONS</span> and <span className="text-red-400">STOP AUTOMATION</span> immediately?</>}
                                </p>
                            </div>

                            <div className="space-y-3">
                                {emergencyResult?.success ? (
                                    <button
                                        onClick={() => window.location.reload()}
                                        className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all shadow-xl shadow-emerald-900/40 active:scale-[0.95]"
                                    >
                                        RELOAD SYSTEM
                                    </button>
                                ) : (
                                    <>
                                        <button
                                            onClick={executeEmergencyProtocol}
                                            disabled={isLiquidating}
                                            className={`w-full py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all shadow-xl active:scale-[0.95] ${isLiquidating
                                                ? 'bg-red-900/50 text-red-400/50 cursor-not-allowed'
                                                : 'bg-red-600 hover:bg-red-500 text-white shadow-red-900/40'
                                                }`}
                                        >
                                            {isLiquidating ? 'PROCESSING...' : emergencyResult?.success === false ? 'RETRY PROTOCOL' : 'EXECUTE PROTOCOL'}
                                        </button>
                                        {!isLiquidating && (
                                            <button
                                                onClick={() => { setShowEmergencyConfirm(false); setEmergencyResult(null); }}
                                                className="w-full bg-white/5 hover:bg-white/10 text-slate-400 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/5"
                                            >
                                                {emergencyResult?.success === false ? 'CLOSE' : 'ABORT MISSION'}
                                            </button>
                                        )}
                                    </>
                                )}
                            </div>

                            <p className="text-center text-[8px] text-red-500/40 font-black uppercase tracking-[0.3em] pt-6">
                                CRITICAL SYSTEM OVERRIDE
                            </p>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >

            {/* Auto Pilot Confirmation Modal */}
            < AnimatePresence >
                {showModeConfirm && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowModeConfirm(false)}
                            className="absolute inset-0 bg-indigo-950/40 backdrop-blur-md"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 10 }}
                            className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] shadow-2xl border-indigo-500/30 bg-black/80"
                        >
                            <div className="text-center space-y-4 mb-8">
                                <div className="w-20 h-20 mx-auto mb-4 bg-indigo-500/10 text-indigo-400 rounded-3xl flex items-center justify-center border border-indigo-500/20 shadow-indigo-500/10">
                                    <Brain className="w-10 h-10 animate-pulse" />
                                </div>
                                <h3 className="text-3xl font-black tracking-tighter text-indigo-400 uppercase">
                                    Engage Pilot
                                </h3>
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] leading-relaxed">
                                    Warning: System will assume <span className="text-indigo-400">FULL CONTROL</span> of execution protocols. Ensure risk guardrails are configured.
                                </p>
                            </div>

                            <div className="space-y-3">
                                <button
                                    onClick={() => executeModeSwitch('AUTO')}
                                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all shadow-xl shadow-indigo-900/40 active:scale-[0.95]"
                                >
                                    CONFIRM ENGAGEMENT
                                </button>
                                <button
                                    onClick={() => setShowModeConfirm(false)}
                                    className="w-full bg-white/5 hover:bg-white/10 text-slate-400 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/5"
                                >
                                    ABORT MISSION
                                </button>
                            </div>

                            <p className="text-center text-[8px] text-indigo-500/40 font-black uppercase tracking-[0.3em] pt-6">
                                AUTONOMOUS EXECUTION PROTOCOL
                            </p>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >

            {/* AI Swarm Training Confirmation Modal */}
            < AnimatePresence >
                {showTrainingConfirm && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setShowTrainingConfirm(false)}
                            className="absolute inset-0 bg-purple-950/40 backdrop-blur-md"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 10 }}
                            className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] shadow-2xl border-purple-500/30 bg-black/80"
                        >
                            <div className="text-center space-y-4 mb-8">
                                <div className="w-20 h-20 mx-auto mb-4 bg-purple-500/10 text-purple-400 rounded-3xl flex items-center justify-center border border-purple-500/20 shadow-purple-500/10">
                                    <Brain className="w-10 h-10 animate-pulse" />
                                </div>
                                <h3 className="text-2xl font-black tracking-tight text-white uppercase">
                                    Rebuild Swarm?
                                </h3>
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] leading-relaxed">
                                    ⚠️ THIS WILL RETRAIN <span className="text-purple-400">ALL 5 AI MODELS</span>.<br /><br />
                                    PROCESS TAKES ~5-15 MINUTES AND REQUIRES SIGNIFICANT COMPUTE.
                                </p>
                            </div>

                            <div className="space-y-3">
                                <button
                                    onClick={handleTriggerTraining}
                                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all shadow-xl shadow-purple-900/40 active:scale-[0.95]"
                                >
                                    START REBUILD
                                </button>
                                <button
                                    onClick={() => setShowTrainingConfirm(false)}
                                    className="w-full bg-white/5 hover:bg-white/10 text-slate-400 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/5"
                                >
                                    ABORT MISSION
                                </button>
                            </div>

                            <p className="text-center text-[8px] text-purple-500/40 font-black uppercase tracking-[0.3em] pt-6">
                                NEURAL SWARM RETRAINING PROTOCOL
                            </p>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >

            {/* Disconnect Confirmation Modal */}
            < AnimatePresence >
                {showDisconnectConfirm && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            onClick={() => setShowDisconnectConfirm(false)}
                            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                            className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] border-white/10 bg-black/90 shadow-2xl"
                        >
                            <div className="text-center space-y-4 mb-8">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-3xl flex items-center justify-center bg-red-500/10 text-red-400 border border-red-500/20">
                                    <LogOut className="w-8 h-8" />
                                </div>
                                <h3 className="text-2xl font-black tracking-tight text-white">DISCONNECT BROKER?</h3>
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest leading-relaxed">
                                    This will <span className="text-red-400">CLEAR ALL CREDENTIALS</span> and revert the system to MOCK mode.
                                </p>
                            </div>
                            <div className="space-y-3">
                                <button
                                    onClick={handleAngelDisconnect}
                                    className="w-full bg-red-500 hover:bg-red-600 text-white py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95"
                                >
                                    CONFIRM DISCONNECT
                                </button>
                                <button
                                    onClick={() => setShowDisconnectConfirm(false)}
                                    className="w-full bg-white/5 hover:bg-white/10 text-slate-400 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all"
                                >
                                    ABORT
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >

            {/* Toast Notification */}
            < AnimatePresence >
                {toast && (
                    <motion.div
                        initial={{ opacity: 0, y: 50, x: '-50%' }}
                        animate={{ opacity: 1, y: 0, x: '-50%' }}
                        exit={{ opacity: 0, y: 20, x: '-50%' }}
                        className="fixed bottom-10 left-1/2 z-[300] px-6 py-4 rounded-2xl border backdrop-blur-xl shadow-2xl flex items-center gap-4 min-w-[300px]"
                        style={{
                            backgroundColor: toast.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                            borderColor: toast.type === 'error' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'
                        }}
                    >
                        <div className={`p-2 rounded-lg ${toast.type === 'error' ? 'bg-red-500/10 text-red-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                            {toast.type === 'error' ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                        </div>
                        <div className="space-y-0.5">
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 leading-none">System Notification</p>
                            <p className="text-xs font-bold text-white">{toast.message}</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence >

            {/* Logout Confirmation Modal */}
            < AnimatePresence >
                {showLogoutConfirm && (
                    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            onClick={() => setShowLogoutConfirm(false)}
                            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                            className="relative w-full max-w-sm glass-panel p-8 rounded-[40px] border-white/10 bg-black/90 shadow-2xl"
                        >
                            <div className="text-center space-y-4 mb-8">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-3xl flex items-center justify-center bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                    <LogOut className="w-8 h-8" />
                                </div>
                                <h3 className="text-2xl font-black tracking-tight text-white">SYSTEM LOGOUT?</h3>
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest leading-relaxed">
                                    End current session and return to secure login portal?
                                </p>
                            </div>
                            <div className="space-y-3">
                                <button
                                    onClick={confirmLogout}
                                    className="w-full bg-indigo-500 hover:bg-indigo-600 text-white py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 shadow-lg shadow-indigo-500/20"
                                >
                                    CONFIRM LOGOUT
                                </button>
                                <button
                                    onClick={() => setShowLogoutConfirm(false)}
                                    className="w-full bg-white/5 hover:bg-white/10 text-slate-400 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all"
                                >
                                    CANCEL
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence >

            <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      `}</style>
        </div >
    );
};

// Simple Error Boundary to prevent blank pages
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error("Dashboard Crash Caught:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0c0d12] text-white p-10 font-mono">
                    <h1 className="text-red-500 text-2xl font-black mb-4 uppercase tracking-tighter">System Critical Failure</h1>
                    <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-2xl max-w-2xl">
                        <p className="text-red-400 mb-4 whitespace-pre-wrap">{this.state.error?.toString()}</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="px-6 py-3 bg-red-500 text-white rounded-xl font-black uppercase tracking-widest hover:bg-red-600 transition-all"
                        >
                            Emergency Reboot
                        </button>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

// Main Export remains Dashboard but wrapped for stability
const Dashboard = () => {
    return (
        <ErrorBoundary>
            <DashboardWithLogic />
        </ErrorBoundary>
    );
};

export default Dashboard;
