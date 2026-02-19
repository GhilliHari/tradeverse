import React, { useState, useEffect, useRef, useCallback } from 'react';
// Tradeverse Dashboard Controller
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
import HUDCard from './ui/HUDCard';
import ScrambleText from './ui/ScrambleText';
import StatusBadge from './StatusBadge';
import ConfidenceGauge from './ConfidenceGauge';
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
import LessonsLearned from './LessonsLearned';
import { Telescope, ScrollText, BookOpen } from 'lucide-react';
import MarketClock from './MarketClock';
import { auth } from '../firebase';


// BASE API URL
const API_URL = "https://tradeverse-1-aosu.onrender.com"; // Forced for production reliability

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 group ${active
            ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/5'
            : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border border-transparent'
            }`}
    >
        <Icon className={`w-5 h-5 ${active ? 'text-indigo-400' : 'text-slate-600 group-hover:text-slate-400'}`} />
        <span className="text-xs font-bold uppercase tracking-widest">{label}</span>
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
const AgentStatus = ({ label, status, icon: Icon, colorClass }) => (
    <div className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-all duration-500 ${status === 'SYNC' ? 'bg-emerald-500/10 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]' : 'bg-white/5 border-white/5 opacity-40'}`}>
        <Icon className={`w-4 h-4 ${status === 'SYNC' ? colorClass : 'text-slate-600'}`} />
        <span className={`text-[8px] font-black uppercase tracking-widest ${status === 'SYNC' ? 'text-white' : 'text-slate-600'}`}>{label}</span>
        <div className={`w-1 h-1 rounded-full ${status === 'SYNC' ? 'bg-emerald-400' : 'bg-slate-700'}`} />
    </div>
);

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
    const [showModeConfirm, setShowModeConfirm] = useState(false);
    const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [toast, setToast] = useState(null);
    const [emergencyResult, setEmergencyResult] = useState(null);
    const [isLiquidating, setIsLiquidating] = useState(false);
    const isConfirmingRef = useRef(false);

    const OWNER_EMAIL = "final_success_verified_v3@tradeverse.ai";
    const [isOwner, setIsOwner] = useState(false);

    const [user, setUser] = useState({ name: 'Guest', initials: 'G', status: 'OFFLINE' });
    const [marketStatus, setMarketStatus] = useState({ isOpen: false, countdown: '00:00:00' });
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
    const [activeSettingsTab, setActiveSettingsTab] = useState('API Keys');
    const [credentials, setCredentials] = useState({
        angel_client_id: '', angel_password: '', angel_api_key: '', angel_totp_key: '',
        kite_api_key: '', kite_access_token: '',
        whatsapp_phone: '', whatsapp_api_key: '',
        telegram_bot_token: '', telegram_chat_id: ''
    });
    const [isConnecting, setIsConnecting] = useState(false);
    const [trustedIPs, setTrustedIPs] = useState([]);
    const [newIP, setNewIP] = useState('');
    const [systemStatus, setSystemStatus] = useState({ backend: false, intelligence: false });

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
        const signal = data.signal;
        if (agent === 'TECH') return analysis.ai_prediction === (signal === 'BUY' ? 'UP' : 'DOWN') ? 'SYNC' : 'IDLE';
        if (agent === 'TFT') return analysis.tft_prediction === (signal === 'BUY' ? 'UP' : 'DOWN') ? 'SYNC' : 'IDLE';
        if (agent === 'RL') return analysis.rl_action === (signal === 'BUY' ? 1 : 2) ? 'SYNC' : 'IDLE';
        if (agent === 'SENT') return analysis.sentiment_label === (signal === 'BUY' ? 'POSITIVE' : 'NEGATIVE') ? 'SYNC' : 'IDLE';
        if (agent === 'OPT') return (signal === 'BUY' ? analysis.pcr < 0.9 : analysis.pcr > 1.1) ? 'SYNC' : 'IDLE';
        return 'IDLE';
    };

    const handleUpdateCredentials = async () => {
        setIsConnecting(true);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000); // 90s timeout for Render cold starts

        // Show "Waking up server" toast if it takes longer than 6 seconds
        const wakeUpToastId = setTimeout(() => {
            showToast("⏳ Waking up server... (this may take a minute)", "info");
        }, 6000);

        try {
            const payload = { ...credentials, active_broker: 'ANGEL' };
            const res = await fetch(`${API_URL}/api/settings/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            clearTimeout(wakeUpToastId);

            if (!res.ok) throw new Error(`Server returned ${res.status}`);

            const data = await res.json();
            if (data.status === 'success') {
                if (data.broker_connected) {
                    showToast("Credentials Updated & Connected to Angel One!", "success");
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
                }
            } else {
                showToast(data.message || "Update Failed", "error");
            }
        } catch (e) {
            clearTimeout(wakeUpToastId); // Ensure wake toast timer is cleared on error
            if (e.name === 'AbortError') {
                showToast("Connection Timed Out (90s). Backend Unresponsive.", "error");
            } else {
                console.error("Credential Update Error:", e);
                showToast(`Network Error: ${e.message}`, "error");
            }
        } finally {
            setIsConnecting(false);
            clearTimeout(timeoutId);
            clearTimeout(wakeUpToastId);
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
            } else {
                console.error("Dashboard: Emergency Protocol Failed", data);
                setEmergencyResult({
                    success: false,
                    message: data.detail || data.message || "Liquidation Failed"
                });
            }
        } catch (e) {
            console.error("Dashboard: Emergency Protocol Connection Error", e);
            setEmergencyResult({
                success: false,
                message: "CRITICAL CONNECTION ERROR during Emergency Stop"
            });
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
            const res = await fetch(`${API_URL}/api/settings`, { headers });
            const data = await res.json();
            setSettings(prev => ({
                ...prev,
                active_broker: data.active_broker,
                env: data.env,
                zerodha_connected: data.zerodha_connected,
                angel_connected: data.angel_connected
            }));
            setIsAutoMode(data.mode === 'AUTO');

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
            const res = await fetch(`${API_URL}/api/settings/trusted-ips`, {
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
            const res = await fetch(`${API_URL}/`);
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
            const res = await fetch(`${API_URL}/api/settings/trusted-ips/add`, {
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
            const res = await fetch(`${API_URL}/api/settings/trusted-ips/remove`, {
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
            const res = await fetch(`${API_URL}/api/settings/update`, {
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

        // IP Protection: Restrict LIVE to Owner
        if (env === 'LIVE' && !isOwner) {
            showToast("Live Environment toggle restricted to Owner account.", "error");
            return;
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
                    console.log("[HANDLE_ENV_SWITCH] Redirecting to Settings > API Keys");
                    setActiveTab('Settings');
                    setActiveSettingsTab('API Keys');
                }
                return;
            }
        }

        try {
            const res = await fetch(`${API_URL}/api/settings/update`, {
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
        // IP Protection: Restrict AUTO PILOT to Owner
        if (!isOwner) {
            showToast("Auto-Pilot Protocol restricted to Owner profile.", "error");
            return;
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
            const res = await fetch(`${API_URL}/api/settings/update`, {
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
            const res = await fetch(`${API_URL}/api/settings/update`, {
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
            const res = await fetch(`${API_URL}/api/settings/whatsapp/test`, {
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
            const res = await fetch(`${API_URL}/api/settings/telegram/test`, {
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
            const res = await fetch(`${API_URL}/api/settings/mode`, {
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
            if (auth?.currentUser?.email === OWNER_EMAIL) {
                setIsOwner(true);
            }
        }
    }, []);

    // Also watch auth state for changes
    useEffect(() => {
        const unsubscribe = auth?.onAuthStateChanged(user => {
            if (user?.email === OWNER_EMAIL) {
                setIsOwner(true);
            } else {
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
            intervalId = setInterval(sendHeartbeat, 5000);
        }

        return () => clearInterval(intervalId);
    }, [isAutoMode, token]);

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
        let priceInterval, optionsInterval, timerInterval;
        if (isLoggedIn) {
            fetchStatus();
            fetchSettings();
            calculateMarketStatus();

            // Immediate fetch on symbol change
            fetchPrice();
            fetchOptionChain();

            priceInterval = setInterval(fetchPrice, 3000);
            optionsInterval = setInterval(fetchOptionChain, 5000);
            timerInterval = setInterval(calculateMarketStatus, 1000);
        }

        return () => {
            if (priceInterval) clearInterval(priceInterval);
            if (optionsInterval) clearInterval(optionsInterval);
            if (timerInterval) clearInterval(timerInterval);
        };
    }, [symbol, isLoggedIn]);

    useEffect(() => {
        let autoInterval;
        if (isLoggedIn && isAutoMode) {
            autoInterval = setInterval(executeAutoPilot, 30000);
        } return () => {
            if (autoInterval) clearInterval(autoInterval);
        };
    }, [isAutoMode, isLoggedIn, symbol]);

    const calculateMarketStatus = () => {
        const now = new Date();
        const day = now.getDay();
        const isWeekend = day === 0 || day === 6;

        const openTime = new Date(now);
        openTime.setHours(9, 15, 0, 0);

        const closeTime = new Date(now);
        closeTime.setHours(15, 30, 0, 0);

        let isOpen = !isWeekend && now >= openTime && now <= closeTime;

        let target;
        if (isOpen) {
            target = closeTime;
        } else {
            target = new Date(now);
            // If after 3:30 or weekend, next open is tomorrow or Monday
            if (now > closeTime || isWeekend) {
                const daysToAdd = day === 5 ? 3 : day === 6 ? 2 : 1;
                target.setDate(now.getDate() + (now > closeTime ? daysToAdd : (day === 6 ? 2 : 1)));
            }
            target.setHours(9, 15, 0, 0);
        }

        const diff = target - now;
        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);

        setMarketStatus({
            isOpen,
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
            const resInit = await fetch(`${API_URL}/`);
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
            }
        } catch (e) {
            // console.warn("Options Fetch Failed");
        }
    };

    const runAgentAnalysis = async () => {
        if (!isLoggedIn) return;
        setIsAnalyzing(true);
        try {
            const res = await fetch(`${API_URL}/api/intelligence/analyze/${symbol}`);
            const result = await res.json();
            setAnalysis(result);
            setData(prev => ({
                ...prev,
                signal: result.final_signal,
                confidence: result.confidence,
                regime: result.regime || 'NOMINAL',
                trade_recommendation: result.trade_recommendation
            }));
        } catch (e) { console.error("Analysis Failed", e); }
        setIsAnalyzing(false);
    };

    const executeAutoPilot = async () => {
        if (!isLoggedIn) return;
        setIsAnalyzing(true);
        console.log("AUTO-PILOT: Initiating Analysis & Execution Cycle...");
        try {
            const res = await fetch(`${API_URL}/api/trading/autopilot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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
                // Refresh orders to show the new trade
                fetchOrders();
            } else if (result.status === 'HOLD') {
                console.log(`AUTO-PILOT: Hold Signal. Reason: ${result.reason}`);
            }

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
    };

    const confirmLogout = async () => {
        setShowLogoutConfirm(false);
        try {
            console.log("Dashboard: Calling logout API...");
            await fetch(`${API_URL}/api/auth/logout`, { method: 'POST' });
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

        const fetchSettings = async (overrideToken = null) => {
            try {
                const res = await fetch(`${API_URL}/api/settings`, {
                    headers: { 'Authorization': `Bearer ${overrideToken || token}` }
                });
                const data = await res.json();

                // Auto-Revert Logic: If backend says LIVE but no connection, force MOCK
                let effectiveEnv = data.env;
                if (data.env === 'LIVE' && !data.angel_connected) {
                    console.warn("State Mismatch: ENV=LIVE but Angel Not Connected. Reverting to MOCK.");
                    effectiveEnv = 'MOCK';

                    // Sync backend asynchronously
                    fetch(`${API_URL}/api/settings/update`, {
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

        fetchSettings(mockToken);
    };

    const handleTriggerTraining = async () => {
        if (!window.confirm("⚠️ This will retrain ALL 5 AI models (Daily, Intraday, TFT, RL, Regime).\n\nThis process takes ~5-15 minutes and requires significant compute.\n\nContinue?")) {
            return;
        }

        setIsTraining(true); // Immediate feedback
        try {
            const res = await fetch(`${API_URL}/api/ai/train`, {
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

        const interval = setInterval(async () => {
            attempts++;
            try {
                const res = await fetch(`${API_URL}/api/ai/train/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (!res.ok) throw new Error("Status check failed");

                const status = await res.json();
                setTrainingStatus(status);
                errorCount = 0; // Reset on success

                if (!status.is_training) {
                    clearInterval(interval);
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
                    clearInterval(interval);
                    setIsTraining(false);
                    setTrainingStatus(prev => ({ ...prev, stage: 'ERROR', message: 'Connection lost during training' }));
                    showToast("❌ Training Status Connection Lost", "error");
                }
            }

            if (attempts >= maxAttempts) {
                clearInterval(interval);
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
            const interval = setInterval(fetchOrders, 5000);
            return () => clearInterval(interval);
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
            <aside className="w-72 glass-panel border-r border-white/10 flex flex-col p-6 hidden lg:flex shadow-[20px_0_50px_rgba(0,0,0,0.3)]">
                <div className="mb-10">
                    <div className="flex items-center justify-between">
                        <h1 className="text-2xl font-black tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent italic">
                            TRADEVERSE
                        </h1>
                    </div>
                </div>

                <div className="flex items-center gap-2 mt-1 px-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">TERMINAL ACTIVE</p>
                </div>

                {/* System Health Panel */}
                <div className="mb-6 space-y-3 px-4 py-4 rounded-xl bg-white/5 border border-white/5 mx-1">
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">System Status</span>
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
                    <div className="flex items-center justify-between cursor-pointer group" onClick={() => handleTabChange('Live Terminal')}>
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
                </nav >
            </aside >

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto custom-scrollbar pb-32 lg:pb-8">
                <div className="p-4 md:p-8 space-y-8">
                    {/* Top Bar */}
                    {/* Top Bar - Floating HUD */}
                    <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 sticky top-0 z-50 py-4 lg:py-2 -mx-2 px-2 bg-[#0c0d12]/80 lg:bg-transparent backdrop-blur-lg lg:backdrop-blur-none transition-all">
                        <div className="glass-premium px-4 lg:px-6 py-2 rounded-full border border-white/15 shadow-2xl flex items-center gap-3 lg:gap-4 backdrop-blur-xl w-full md:w-auto">
                            <h2 className="text-lg lg:text-xl font-black text-white tracking-widest uppercase truncate max-w-[120px] lg:max-w-none">{activeTab}</h2>
                            <div className="h-4 w-[1px] bg-white/10" />
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
                                        setSearchInput(''); // Auto-clear on focus for better UX
                                        if (searchResults.length > 0) setShowResults(true);
                                    }}
                                    onBlur={() => {
                                        // Delay hiding to allow click
                                        setTimeout(() => {
                                            if (!searchInput) setSearchInput(symbol); // Revert to current symbol if empty
                                            setShowResults(false);
                                        }, 200);
                                    }}
                                    placeholder="SEARCH NSE..."
                                    className="bg-transparent border-none outline-none text-white font-black w-24 lg:w-32 focus:ring-0 placeholder:text-slate-700 text-xs lg:text-sm"
                                />
                                {searchInput && searchInput !== symbol && (
                                    <button
                                        onClick={() => { setSearchInput(''); setShowResults(false); }}
                                        className="absolute right-8 text-slate-500 hover:text-white transition-colors"
                                    >
                                        <LogOut className="w-3 h-3 rotate-90" /> {/* Using a simple icon as clear */}
                                    </button>
                                )}
                                <Search className="w-3 h-3 text-slate-600 group-focus-within:text-indigo-400 transition-colors" />

                                {/* Search Results Dropdown */}
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

                        <div className="flex items-center gap-3">
                            {/* Controls Group */}
                            <div className="flex items-center gap-2 md:w-auto">
                                {/* Auto Pilot Switch */}
                                <ControlToggle
                                    label={isAutoMode ? "AUTO" : "MANUAL"}
                                    active={isAutoMode}
                                    onClick={handleModeToggle}
                                    color="emerald"
                                />

                                {/* Emergency Kill Switch */}
                                <button
                                    onClick={handleEmergencyStop}
                                    className="flex-shrink-0 px-3 lg:px-4 py-1.5 h-[38px] rounded-xl border border-red-500/20 bg-red-500/5 hover:bg-red-500/20 hover:border-red-500/40 transition-all flex items-center gap-2 lg:gap-3 hover:scale-105 active:scale-95 cursor-pointer z-50 group"
                                    title="CRITICAL EMERGENCY STOP"
                                >
                                    <AlertTriangle className="w-3 h-3 lg:w-4 lg:h-4 text-red-500/60 group-hover:text-red-500" />
                                    <span className="text-[9px] lg:text-[10px] font-black uppercase tracking-[0.15em] lg:tracking-[0.2em] text-red-500/60 group-hover:text-red-500">KILL SWITCH</span>
                                </button>
                            </div>

                            {/* Market Clock & Status Integration */}
                            <div className="mr-2">
                                <MarketClock isOpen={marketStatus.isOpen} />
                            </div>

                            {/* System Status Badges */}
                            <div className="flex gap-2">
                                <StatusBadge
                                    label="SYSTEM"
                                    status={riskStatus.circuit_breaker_status === 'NOMINAL' ? 'NOMINAL' : 'HALTED'}
                                    color={riskStatus.circuit_breaker_status === 'NOMINAL' ? 'emerald' : 'red'}
                                    pulse={riskStatus.circuit_breaker_status !== 'NOMINAL'}
                                />


                                {/* User Profile Badge */}
                                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg border border-white/10 h-[38px]">
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center font-black text-[9px] border ${user.status === 'ONLINE' ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-slate-700/50 text-slate-400 border-white/5'}`}>
                                        {user.initials}
                                    </div>
                                    <div className="flex flex-col justify-center">
                                        <span className={`text-[10px] font-black uppercase tracking-wider ${user.status === 'ONLINE' ? 'text-indigo-400' : 'text-slate-500'}`}>
                                            {user.name}
                                        </span>
                                    </div>
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
                        </div>
                    </header>

                    {activeTab === 'Live Terminal' ? (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            {/* Tactical Monitor Box (Side-by-Side) */}
                            <div className="lg:col-span-3">
                                <HUDCard title="TACTICAL MONITOR" neonColor="indigo" className="relative">

                                    <div className="pt-10 p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                                        {/* System Health Path */}
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className={`p-3 rounded-xl border transition-all duration-500 ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : 'bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]'}`}>
                                                        <Shield className={`w-6 h-6 ${riskStatus.circuit_breaker_status !== 'NOMINAL' ? 'animate-pulse' : ''}`} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-sm font-black text-white uppercase tracking-wider italic">System Integrity</h3>
                                                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Risk Guardrail Status</p>
                                                    </div>
                                                </div>
                                                <div className={`px-4 py-2 rounded-lg border font-black text-[10px] tracking-widest transition-all duration-500 ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse'}`}>
                                                    {riskStatus.circuit_breaker_status === 'NOMINAL' ? 'NOMINAL' : 'HALTED'}
                                                </div>
                                            </div>

                                            <div className="bg-white/5 border border-white/5 p-4 rounded-2xl relative">
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Perimeter Breach Check</span>
                                                    <span className="text-[10px] font-mono text-white italic">₹{riskStatus.current_daily_loss?.toFixed(0)} / ₹{riskStatus.daily_loss_limit}</span>
                                                </div>
                                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${Math.min(((riskStatus.current_daily_loss || 0) / (riskStatus.daily_loss_limit || 1)) * 100, 100) || 0}%` }}
                                                        className={`h-full transition-all duration-1000 ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'bg-emerald-500/50' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'}`}
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Market Analysis Path */}
                                        <div className="space-y-4 border-l border-white/5 pl-0 md:pl-8">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <div className={`p-3 rounded-xl border transition-all duration-500 ${data.regime === 'NOMINAL' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]' : data.regime === 'VOLATILE' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.2)]' : 'bg-red-500/10 text-red-500 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]'}`}>
                                                        <Globe className={`w-6 h-6 ${data.regime !== 'NOMINAL' ? 'animate-spin-slow' : ''}`} />
                                                    </div>
                                                    <div>
                                                        <h3 className="text-sm font-black text-white uppercase tracking-wider italic">Market Regime</h3>
                                                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Structural State Engine</p>
                                                    </div>
                                                </div>
                                                <div className={`px-4 py-2 rounded-lg border font-black text-[10px] tracking-widest transition-all duration-500 ${data.regime === 'NOMINAL' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : data.regime === 'VOLATILE' ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' : 'bg-red-500/20 border-red-500/50 text-red-400 animate-pulse'}`}>
                                                    {data.regime}
                                                </div>
                                            </div>

                                            <div className="bg-white/5 border border-white/5 p-4 rounded-2xl relative">
                                                <div className="flex justify-between items-center mb-3">
                                                    <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Committee Sync Status</span>
                                                    <span className="text-[10px] font-mono text-white italic">{data.regime === 'NOMINAL' ? '3/5 REQ' : data.regime === 'VOLATILE' ? '4/5 REQ' : '5/5 REQ'}</span>
                                                </div>
                                                <div className="grid grid-cols-5 gap-2">
                                                    <AgentStatus label="TECH" status={getAgentStatus('TECH')} icon={TrendingUp} colorClass="text-emerald-400" />
                                                    <AgentStatus label="TFT" status={getAgentStatus('TFT')} icon={Activity} colorClass="text-purple-400" />
                                                    <AgentStatus label="RL" status={getAgentStatus('RL')} icon={Zap} colorClass="text-amber-400" />
                                                    <AgentStatus label="SENT" status={getAgentStatus('SENT')} icon={Brain} colorClass="text-blue-400" />
                                                    <AgentStatus label="OPT" status={getAgentStatus('OPT')} icon={ListOrdered} colorClass="text-indigo-400" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </HUDCard>
                            </div>

                            {/* Tactical Command Row (Swarm + Risk) */}
                            <div className="lg:col-span-3 grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-2">
                                    <HUDCard title="AGENT SWARM" neonColor="purple">
                                        <div className="p-6">
                                            <div className="flex items-center gap-2 pb-4 border-b border-purple-500/20">
                                                <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
                                                    <Zap className="w-5 h-5 animate-pulse" />
                                                </div>
                                                <h3 className="font-black text-[10px] uppercase tracking-[0.2em] text-slate-400 italic">Live Consensus Matrix</h3>
                                            </div>

                                            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar mt-6">
                                                <AnimatePresence mode="wait">
                                                    {analysis && analysis.sentiment_analysis ? (
                                                        <motion.div
                                                            key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3"
                                                        >
                                                            {[
                                                                { role: "Sentiment", text: analysis.sentiment_analysis, icon: Brain, color: "text-blue-400 border-blue-500/20 bg-blue-500/10" },
                                                                { role: "Technical", text: analysis.technical_analysis || "Processing technicals...", icon: TrendingUp, color: "text-emerald-400 border-emerald-500/20 bg-emerald-500/10" },
                                                                { role: "Options (OI/PCR)", text: `PCR: ${analysis.pcr?.toFixed(2)} | OI Support: ${analysis.pcr < 0.9 ? 'STRONG' : 'NEUTRAL'}. Institutional positioning detected.`, icon: ListOrdered, color: "text-indigo-400 border-indigo-500/20 bg-indigo-500/10" },
                                                                { role: "Temporal (TFT)", text: `Prediction: ${analysis.tft_prediction || 'SYNCHRONIZING'}. Deep Sequence Context active.`, icon: Activity, color: "text-purple-400 border-purple-500/20 bg-purple-500/10" },
                                                                { role: "Sniper (RL)", text: `Action Code: ${analysis.rl_action || 0}. Timing optimizer targeting high-velocity entries.`, icon: Zap, color: "text-amber-400 border-amber-500/20 bg-amber-500/10" },
                                                                { role: "Risk Guard", text: analysis.risk_approval === undefined ? "Risk scan pending..." : (analysis.risk_approval ? "Risk Parameters Nominal. Trade Authorized." : "CRITICAL RISK DETECTED. HALTING."), icon: Shield, color: analysis.risk_approval ? "text-emerald-400 border-emerald-500/20 bg-emerald-500/10" : "text-red-400 border-red-500/20 bg-red-500/10" },
                                                            ].map((report, idx) => (
                                                                <div key={idx} className={`p-5 rounded-2xl border transition-all hover:bg-white/[0.07] shadow-xl ${report.color.split(' ').slice(1).join(' ')}`}>
                                                                    <div className={`flex items-center justify-between text-[10px] font-black uppercase tracking-widest mb-3 ${report.color.split(' ')[0]}`}>
                                                                        <div className="flex items-center gap-2">
                                                                            <report.icon className="w-3.5 h-3.5" /> {report.role}
                                                                        </div>
                                                                        <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                                                                    </div>
                                                                    <div className="bg-black/20 p-3 rounded-lg border border-white/5">
                                                                        <p className="text-[10px] text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">{report.text}</p>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </motion.div>
                                                    ) : (
                                                        <div className="h-40 flex flex-col items-center justify-center text-slate-700">
                                                            <Activity className="w-10 h-10 opacity-10 mb-2 animate-pulse" />
                                                            <p className="text-[10px] font-black tracking-widest text-indigo-500/40">AWAITING FEED</p>
                                                        </div>
                                                    )}
                                                </AnimatePresence>

                                                {/* Disconnect Confirmation Modal */}
                                                <AnimatePresence>
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
                                                </AnimatePresence>

                                                {/* Toast Notification */}
                                                <AnimatePresence>
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
                                                </AnimatePresence>
                                            </div>
                                        </div>
                                    </HUDCard>
                                </div>

                                <div className="lg:col-span-1">
                                    <HUDCard title="RISK PERIMETER" neonColor="red" className="bg-red-500/[0.02] border-red-500/10 h-full">
                                        <div className="p-6">
                                            <div className="flex items-center gap-3 mb-6">
                                                <div className="p-3 bg-red-500/10 text-red-500 rounded-2xl shadow-[0_0_15px_rgba(239,68,68,0.2)] border border-red-500/20">
                                                    <AlertTriangle className="w-6 h-6 animate-pulse" />
                                                </div>
                                                <div>
                                                    <h3 className="font-black text-xs uppercase tracking-widest text-red-400 neon-text-red">Protocol & Guardrails</h3>
                                                    <p className="text-[9px] font-bold text-slate-600 uppercase tracking-tighter">Active System Defense</p>
                                                </div>
                                            </div>

                                            {/* Side-by-Side Mode Matrix */}
                                            <div className="grid grid-cols-2 gap-3 mb-6">
                                                <div className={`p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all duration-500 ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-red-500/10 border-red-500/20'}`}>
                                                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">System State</span>
                                                    <div className={`text-[10px] font-black tracking-tighter ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'text-emerald-400' : 'text-red-400 animate-pulse'}`}>
                                                        {riskStatus.circuit_breaker_status === 'NOMINAL' ? 'STABLE' : 'HALTED'}
                                                    </div>
                                                </div>
                                                <div className={`p-3 rounded-xl border flex flex-col items-center justify-center text-center transition-all duration-500 ${data.regime === 'NOMINAL' ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-amber-500/5 border-amber-500/20'}`}>
                                                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Market Regime</span>
                                                    <div className={`text-[10px] font-black tracking-tighter ${data.regime === 'NOMINAL' ? 'text-emerald-400' : data.regime === 'VOLATILE' ? 'text-amber-400' : 'text-red-400'}`}>
                                                        {data.regime}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-4 pt-4 border-t border-white/5">
                                                <div className="flex justify-between items-center text-[11px] font-bold px-1">
                                                    <span className="text-slate-500 uppercase tracking-[0.1em]">Daily Loss Perimeter</span>
                                                    <span className="text-white font-black text-xs italic">
                                                        ₹<ScrambleText text={riskStatus.current_daily_loss?.toLocaleString('en-IN') || '0'} /> / ₹{riskStatus.daily_loss_limit?.toLocaleString('en-IN')}
                                                    </span>
                                                </div>
                                                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden p-[2px]">
                                                    <div
                                                        className={`h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_currentColor] ${riskStatus.circuit_breaker_status === 'NOMINAL' ? 'bg-emerald-500/50 text-emerald-500' : 'bg-red-500 text-red-500'}`}
                                                        style={{ width: `${Math.min(((riskStatus.current_daily_loss || 0) / (riskStatus.daily_loss_limit || 1)) * 100, 100) || 0}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </HUDCard>
                                </div>
                            </div>

                            {/* Market Mood Index Row */}
                            <div className="lg:col-span-3">
                                <MarketMoodIndex />
                            </div>

                            {/* Charts & Signals */}
                            <div className="lg:col-span-2 space-y-6">
                                <div className="glass-premium holographic-border p-6 rounded-[32px] overflow-hidden relative group transition-all duration-500 hover:shadow-[0_0_30px_rgba(99,102,241,0.1)] border border-white/10">
                                    <div className="flex justify-between items-end mb-8 relative z-10">
                                        <div>
                                            <span className="text-slate-500 text-xs font-bold uppercase tracking-widest">Live Tick Streams</span>
                                            <div className="flex items-baseline gap-2 mt-1">
                                                <h2 className="text-5xl font-black tabular-nums tracking-tighter">₹{data.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</h2>
                                                <span className="text-emerald-400/80 font-bold text-sm tracking-widest">LIVE_FEED</span>
                                            </div>
                                        </div>

                                        <div className="text-right">
                                            <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-1">Exchange</div>
                                            <div className="text-lg font-black text-indigo-400">NSE INDIA</div>
                                        </div>
                                    </div>

                                    <div className="h-[280px] w-full -mx-4">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData}>
                                                <defs>
                                                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} />
                                                <XAxis
                                                    dataKey="time"
                                                    hide={true} // Hide labels for clean look, but keep axis structure
                                                />
                                                <YAxis
                                                    domain={['auto', 'auto']}
                                                    orientation="right"
                                                    tick={{ fontSize: 10, fill: '#64748b' }}
                                                    axisLine={false}
                                                    tickLine={false}
                                                    width={40}
                                                />
                                                <Tooltip
                                                    contentStyle={{ backgroundColor: '#161720', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                                                    itemStyle={{ color: '#fff' }}
                                                    labelStyle={{ color: '#94a3b8' }}
                                                />
                                                <Area
                                                    type="monotone"
                                                    dataKey="price"
                                                    stroke="#6366f1"
                                                    strokeWidth={3}
                                                    fillOpacity={1}
                                                    fill="url(#colorPrice)"
                                                    animationDuration={500}
                                                    isAnimationActive={true}
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </div>
                            </div>

                            <div className="lg:col-span-1">
                                <HUDCard title="CORTEX.AI" neonColor="purple" className="h-full">
                                    <div className="p-5 h-full flex flex-col">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg border border-purple-500/20 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                                                <Brain className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h3 className="text-xs font-black text-white uppercase tracking-wider neon-text-indigo">Neural Command</h3>
                                                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Inference v9.0</p>
                                            </div>
                                        </div>

                                        <div className="space-y-6 relative z-10 flex-1 flex flex-col">
                                            <div className="bg-white/[0.03] p-6 rounded-2xl border border-white/5 flex items-center justify-between">
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="text-slate-500 text-[10px] font-black uppercase tracking-widest">Signal Output</span>
                                                        {isAnalyzing && (
                                                            <div className="flex items-center gap-2 text-indigo-400">
                                                                <RefreshCw className="w-3 h-3 animate-spin" />
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className={`text-4xl font-black tracking-tighter ${data.signal === 'BUY' ? 'text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.4)]' :
                                                        data.signal === 'SELL' ? 'text-red-400 shadow-[0_0_20px_rgba(244,63,94,0.4)]' : 'text-amber-400'
                                                        }`}>
                                                        {isAnalyzing ? <span className="opacity-50 italic text-xl">SYNC...</span> : data.signal}
                                                    </div>
                                                </div>

                                                <ConfidenceGauge score={data.confidence || 0} />
                                            </div>

                                            <div className="bg-black/40 p-5 border border-white/5 relative overflow-hidden rounded-2xl flex-1 min-h-[100px]">
                                                <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-white/10" />
                                                <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-indigo-500/50" />

                                                <div className="flex items-center gap-2 mb-3">
                                                    <Terminal className="w-3.5 h-3.5 text-emerald-500" />
                                                    <span className="text-[10px] font-black text-emerald-500/70 uppercase tracking-widest">LOG OUTPUT</span>
                                                </div>
                                                <p className="text-[11px] font-mono text-emerald-400/80 leading-relaxed">
                                                    {">"} {data.trade_recommendation?.reasoning || "Neural core idle. Awaiting market volatility signal..."}
                                                </p>
                                            </div>

                                            {!isAnalyzing && (
                                                <button onClick={runAgentAnalysis} className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white border border-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.4)] text-[10px] font-black uppercase tracking-[0.2em] transition-all clip-path-polygon active:scale-95">
                                                    INITIALIZE SCAN
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </HUDCard>
                            </div>

                            {/* Option Chain / Strikes Section */}
                            <div className="lg:col-span-3">
                                <HUDCard title="DERIVATIVE MATRIX" neonColor="indigo" className="space-y-4">
                                    <div className="p-6">
                                        <div className="flex justify-between items-center border-b border-indigo-500/20 pb-4">
                                            <div className="flex items-center gap-2">
                                                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                                                    <ListOrdered className="w-5 h-5" />
                                                </div>
                                                <h3 className="font-black text-sm uppercase tracking-widest text-slate-300 italic">Option Chain: {symbol} Strikes</h3>
                                            </div>
                                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Expiries: Weekly | Monthly</span>
                                        </div>

                                        <div className="overflow-x-auto mt-4">
                                            <table className="w-full text-left border-separate border-spacing-y-2">
                                                <thead>
                                                    <tr className="text-[10px] font-black uppercase text-slate-600 tracking-widest">
                                                        <th className="px-4 py-2">CALLS (CE)</th>
                                                        <th className="px-4 py-2">OI (CE)</th>
                                                        <th className="px-4 py-2 text-center bg-indigo-500/5 rounded-t-xl">STRIKE PRICE</th>
                                                        <th className="px-4 py-2 text-right">OI (PE)</th>
                                                        <th className="px-4 py-2 text-right">PUTS (PE)</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="text-xs font-bold tabular-nums">
                                                    {(Array.isArray(optionChain) ? optionChain : []).map((item, idx) => {
                                                        const isATM = data && data.price && item && item.strike ? Math.abs(data.price - item.strike) < 100 : false;
                                                        return (
                                                            <tr key={idx} className={`group hover:bg-white/5 transition-all ${isATM ? 'bg-indigo-500/10' : ''}`}>
                                                                <td className="px-4 py-3 text-emerald-400">₹{item.ce_premium}</td>
                                                                <td className="px-4 py-3 text-slate-500">{(item.oi_ce / 1000).toFixed(1)}k</td>
                                                                <td className={`px-4 py-3 text-center transition-all ${isATM ? 'bg-indigo-500 text-white shadow-lg font-black scale-105 rounded-xl border border-indigo-400/30 shadow-[0_0_15px_rgba(99,102,241,0.3)]' : 'bg-white/5 text-slate-400 group-hover:text-white'}`}>
                                                                    {item.strike}
                                                                </td>
                                                                <td className="px-4 py-3 text-right text-slate-500">{(item.oi_pe / 1000).toFixed(1)}k</td>
                                                                <td className="px-4 py-3 text-right text-red-400">₹{item.pe_premium}</td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </HUDCard>
                            </div>

                        </div>
                    ) : activeTab.toLowerCase() === 'settings' ? (
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

                                            <div className="pt-8">
                                                <button
                                                    onClick={handleUpdateCredentials}
                                                    disabled={isConnecting}
                                                    className={`w-full py-4 ${isConnecting ? 'bg-indigo-500/50 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500'} text-white rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-3 active:scale-95`}
                                                >
                                                    {isConnecting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                                                    {isConnecting ? 'Connecting to Exchange...' : 'Connect Angel One'}
                                                </button>


                                                {settings.angel_connected && (
                                                    <button
                                                        onClick={() => setShowDisconnectConfirm(true)}
                                                        className="w-full mt-4 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-2xl text-xs font-black uppercase tracking-widest transition-all shadow-lg flex items-center justify-center gap-2"
                                                    >
                                                        <LogOut className="w-4 h-4" /> Disconnect Angel One
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : activeSettingsTab === 'Intelligence' ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                                        <div className="flex items-start gap-6 mb-8">
                                            <div className="p-4 bg-purple-500/10 rounded-3xl text-purple-400 border border-purple-500/20 shadow-lg shadow-purple-500/10">
                                                <Brain className="w-8 h-8" />
                                            </div>
                                            <div>
                                                <h3 className="text-2xl font-black text-white tracking-tight">AI Swarm Intelligence</h3>
                                                <p className="text-slate-500 text-sm font-medium mt-2 max-w-md">Retrain the entire neural core - 5 AI models working in harmony. Training takes ~5-15 minutes.</p>
                                            </div>
                                        </div>

                                        {/* Training Control Panel */}
                                        <div className="glass-panel p-8 rounded-3xl space-y-6 border border-purple-500/10">
                                            <div className="flex items-center justify-between mb-6">
                                                <div>
                                                    <h4 className="text-lg font-black text-white">Training Status</h4>
                                                    <p className="text-[10px] font-black uppercase text-slate-500 mt-1 tracking-widest">{trainingStatus.stage}</p>
                                                </div>
                                                <button
                                                    onClick={handleTriggerTraining}
                                                    disabled={isTraining}
                                                    className={`px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all shadow-lg ${isTraining
                                                        ? 'bg-slate-500/20 text-slate-500 cursor-not-allowed'
                                                        : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-purple-500/40'
                                                        }`}
                                                >
                                                    {isTraining ? '⏳ Training...' : '🧠 Rebuild Swarm'}
                                                </button>
                                            </div>

                                            {/* Progress Bar */}
                                            {trainingStatus.progress > 0 && (
                                                <div className="space-y-3">
                                                    <div className="flex items-center justify-between text-xs mb-1">
                                                        <span className="font-mono text-slate-400">{trainingStatus.message}</span>
                                                        <span className="font-mono text-purple-400 font-black">{trainingStatus.progress}%</span>
                                                    </div>
                                                    <div className="w-full h-3 bg-black/30 rounded-full overflow-hidden border border-white/5">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-purple-600 to-indigo-600 transition-all duration-1000 ease-out shadow-lg shadow-purple-500/50"
                                                            style={{ width: `${trainingStatus.progress}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            )}

                                            {/* Training Stages */}
                                            <div className="grid grid-cols-5 gap-3 mt-6">
                                                {[
                                                    { name: 'Daily', key: 'DAILY_STRATEGIST', icon: TrendingUp },
                                                    { name: 'Intraday', key: 'INTRADAY_SNIPER', icon: Zap },
                                                    { name: 'TFT', key: 'TFT_TRANSFORMER', icon: Activity },
                                                    { name: 'RL', key: 'RL_OPTIMIZER', icon: Brain },
                                                    { name: 'Regime', key: 'REGIME_ENGINE', icon: Shield }
                                                ].map((stage) => {
                                                    const isComplete = ['DAILY_STRATEGIST', 'INTRADAY_SNIPER', 'TFT_TRANSFORMER', 'RL_OPTIMIZER', 'REGIME_ENGINE'].indexOf(stage.key) < ['DAILY_STRATEGIST', 'INTRADAY_SNIPER', 'TFT_TRANSFORMER', 'RL_OPTIMIZER', 'REGIME_ENGINE'].indexOf(trainingStatus.stage);
                                                    const isActive = trainingStatus.stage === stage.key;
                                                    const Icon = stage.icon;

                                                    return (
                                                        <div
                                                            key={stage.key}
                                                            className={`p-4 rounded-2xl text-center transition-all ${isComplete ? 'bg-emerald-500/10 border border-emerald-500/30' :
                                                                isActive ? 'bg-purple-500/10 border border-purple-500/30 animate-pulse' :
                                                                    'bg-black/20 border border-white/5'
                                                                }`}
                                                        >
                                                            <Icon className={`w-6 h-6 mx-auto mb-2 ${isComplete ? 'text-emerald-400' :
                                                                isActive ? 'text-purple-400' :
                                                                    'text-slate-600'
                                                                }`} />
                                                            <p className={`text-[10px] font-black uppercase tracking-widest ${isComplete ? 'text-emerald-400' :
                                                                isActive ? 'text-purple-400' :
                                                                    'text-slate-600'
                                                                }`}>{stage.name}</p>
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            {/* Model Metrics (if available) */}
                                            {modelMetrics && (
                                                <div className="mt-6 p-6 bg-black/20 rounded-2xl border border-white/5">
                                                    <h5 className="text-xs font-black uppercase text-slate-500 tracking-widest mb-4">Latest Metrics</h5>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        {modelMetrics.daily && (
                                                            <>
                                                                <div>
                                                                    <p className="text-[10px] text-slate-500 mb-1">Daily Precision</p>
                                                                    <p className="text-lg font-mono font-black text-emerald-400">{(modelMetrics.daily.precision * 100).toFixed(1)}%</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-[10px] text-slate-500 mb-1">Daily F1 Score</p>
                                                                    <p className="text-lg font-mono font-black text-cyan-400">{modelMetrics.daily.f1.toFixed(3)}</p>
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
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
            <AnimatePresence>
                {showLogin && (
                    <LoginModal
                        isOpen={showLogin}
                        onClose={() => setShowLogin(false)}
                        onLogin={(authToken) => {
                            setIsLoggedIn(true);
                            setToken(authToken); // Store valid token
                            setUser({ name: 'Pro Trader', initials: 'PT', status: 'ONLINE', broker: 'ANGEL ONE' });
                            playInitSound();
                        }}
                        onGuestLogin={handleGuestLogin}
                    />
                )}
            </AnimatePresence>

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
            <AnimatePresence>
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
            </AnimatePresence>

            {/* Disconnect Confirmation Modal */}
            <AnimatePresence>
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
            </AnimatePresence>

            {/* Toast Notification */}
            <AnimatePresence>
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
            </AnimatePresence>

            {/* Logout Confirmation Modal */}
            <AnimatePresence>
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
            </AnimatePresence>

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
