import React, { useState, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { getApiUrl, API_URL } from '../config/api';


const ICICIDirectTicker = ({ currentSymbol, onSelectSymbol }) => {
    const [indices, setIndices] = useState({
        nifty: {
            symbol: 'NSE:NIFTY',
            name: 'NIFTY 50',
            price: 24471.70,
            change: -112.10,
            pct: -0.46,
            prevPrice: 24583.80,
            flash: null, // 'up' | 'down' | null
        },
        banknifty: {
            symbol: 'NSE:BANKNIFTY',
            name: 'BANK NIFTY',
            price: 57446.25,
            change: -240.70,
            pct: -0.42,
            prevPrice: 57686.95,
            flash: null, // 'up' | 'down' | null
        }
    });

    const flashTimeoutRef = useRef({});

    // Fetch Live Market Ticks from Backend API
    useEffect(() => {
        const fetchLiveTicks = async () => {
            try {
                const res = await fetch(`${API_URL}/api/market/indices`);
                if (!res.ok) throw new Error('API fetch failed');
                const data = await res.json();

                setIndices(prev => {
                    const updateItem = (key, defaultSimVal) => {
                        const item = prev[key];
                        const fetched = data[key];
                        if (fetched && fetched.price) {
                            const newPrice = fetched.price;
                            const priceDiff = newPrice - item.price;
                            let flashType = null;
                            if (priceDiff > 0.01) flashType = 'up';
                            else if (priceDiff < -0.01) flashType = 'down';

                            return {
                                ...item,
                                price: newPrice,
                                change: fetched.change,
                                pct: fetched.pct,
                                prevPrice: fetched.prevPrice,
                                flash: flashType || item.flash
                            };
                        }
                        return item;
                    };

                    return {
                        nifty: updateItem('nifty', 24471.70),
                        banknifty: updateItem('banknifty', 57446.25)
                    };
                });
            } catch (err) {
                console.error("Live ticker update error:", err);
            }
        };

        fetchLiveTicks();
        const interval = setInterval(fetchLiveTicks, 3000);
        return () => clearInterval(interval);
    }, []);

    // Clear flash effects after 600ms
    useEffect(() => {
        ['nifty', 'banknifty'].forEach(key => {
            if (indices[key].flash) {
                clearTimeout(flashTimeoutRef.current[key]);
                flashTimeoutRef.current[key] = setTimeout(() => {
                    setIndices(prev => ({
                        ...prev,
                        [key]: { ...prev[key], flash: null }
                    }));
                }, 600);
            }
        });
    }, [indices.nifty.price, indices.banknifty.price]);

    return (
        <div className="flex items-center gap-2 shrink-0 bg-black/40 border border-white/10 px-2.5 py-1 rounded-full backdrop-blur-xl shadow-2xl">
            {/* Live Streaming Badge */}
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="text-[9px] font-black uppercase tracking-widest text-emerald-300">LIVE NSE</span>
            </div>

            {/* Tickers */}
            {[indices.nifty, indices.banknifty].map((item) => {
                const isActive = currentSymbol?.includes(item.name.replace(' ', ''));
                const isPositive = item.change >= 0;
                
                // ICICI Direct Flash Effect Classes
                let flashClass = "bg-white/5 border-white/10 text-slate-200 hover:bg-white/10";
                if (item.flash === 'up') {
                    flashClass = "bg-emerald-500/30 border-emerald-400 text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.5)] scale-105 transition-all duration-150";
                } else if (item.flash === 'down') {
                    flashClass = "bg-rose-500/30 border-rose-400 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.5)] scale-105 transition-all duration-150";
                } else if (isActive) {
                    flashClass = "bg-indigo-500/20 border-indigo-500/40 text-indigo-200 shadow-[0_0_12px_rgba(99,102,241,0.2)]";
                }

                return (
                    <button
                        key={item.symbol}
                        onClick={() => onSelectSymbol(item.symbol)}
                        className={`px-3 py-1 rounded-full border transition-all flex items-center gap-2 cursor-pointer ${flashClass}`}
                        title={`Click to switch chart to ${item.name}`}
                    >
                        {/* Index Symbol */}
                        <span className="text-[10px] font-black tracking-wider uppercase text-slate-300">
                            {item.name}
                        </span>

                        {/* Live Price */}
                        <span className="text-[11px] font-black font-mono text-white tracking-tight">
                            {item.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>

                        {/* Points & Percentage Badge */}
                        <div className={`flex items-center gap-0.5 text-[9px] font-bold px-1.5 py-0.5 rounded-full ${isPositive ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'}`}>
                            {isPositive ? (
                                <TrendingUp className="w-2.5 h-2.5 text-emerald-400" />
                            ) : (
                                <TrendingDown className="w-2.5 h-2.5 text-rose-400" />
                            )}
                            <span>{isPositive ? '+' : ''}{item.change.toFixed(2)} ({isPositive ? '+' : ''}{item.pct.toFixed(2)}%)</span>
                        </div>
                    </button>
                );
            })}
        </div>
    );
};

export default ICICIDirectTicker;
