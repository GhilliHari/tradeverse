import React, { useState, useEffect } from 'react';
import HUDCard from './ui/HUDCard';

const MarketMoodIndex = () => {
    const [mmiData, setMmiData] = useState({
        mmi: 50,
        label: 'NEUTRAL',
        status: 'loading'
    });

    useEffect(() => {
        const fetchMMI = async () => {
            try {
                const response = await fetch('/api/market/mmi');
                const data = await response.json();
                setMmiData({ ...data, status: 'live' });
            } catch (error) {
                console.error('Failed to fetch MMI:', error);
                setMmiData({
                    mmi: 50,
                    label: 'NEUTRAL',
                    status: 'error'
                });
            }
        };

        fetchMMI();
        const interval = setInterval(fetchMMI, 60000);
        return () => clearInterval(interval);
    }, []);

    const value = mmiData.mmi;
    // Full circle: 0° at top, clockwise
    // Map 0-100 to 0-360 degrees, starting from left (9 o'clock = -90deg)
    const angle = (value / 100) * 360 - 90;

    // Determine color based on backend thresholds:
    // 0-20 (Ext Fear), 20-40 (Fear), 40-60 (Neutral), 60-80 (Greed), 80-100 (Ext Greed)
    const getStatusColor = (val) => {
        if (val < 20) return '#3b82f6'; // Extreme Fear (Blue)
        if (val < 40) return '#60a5fa'; // Fear (Light Blue)
        if (val < 60) return '#94a3b8'; // Neutral (Slate)
        if (val < 80) return '#f59e0b'; // Greed (Orange)
        return '#ef4444'; // Extreme Greed (Red)
    };

    const activeColor = getStatusColor(value);

    // Determine active zone for highlighting
    const activeZone =
        value < 20 ? 'extremeFear' :
            value < 40 ? 'fear' :
                value < 60 ? 'neutral' :
                    value < 80 ? 'greed' : 'extremeGreed';

    return (
        <HUDCard title="MARKET MOOD INDEX (MMI)" neonColor="purple" className="h-[500px]">
            <div className="p-8 flex flex-col items-center justify-center h-full bg-black/20 rounded-lg backdrop-blur-sm">

                {/* Gauge Container */}
                <div className="relative w-96 h-96 mb-8 group">
                    {/* Ambient Glow behind the gauge */}
                    <div
                        className="absolute inset-0 rounded-full blur-[100px] opacity-20 transition-colors duration-1000"
                        style={{ backgroundColor: activeColor }}
                    />

                    <svg viewBox="0 0 400 400" className="w-full h-full relative z-10 drop-shadow-2xl">
                        <defs>
                            {/* Neon Glow Filter */}
                            <filter id="neon-glow" x="-50%" y="-50%" width="200%" height="200%">
                                <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>

                            {/* Soft Glow Filter */}
                            <filter id="soft-glow" x="-50%" y="-50%" width="200%" height="200%">
                                <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>

                            {/* Gradients for Zones */}
                            <linearGradient id="extremeFearGradient" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#1e3a8a" />
                                <stop offset="100%" stopColor="#3b82f6" />
                            </linearGradient>

                            <linearGradient id="fearGradient" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#2563eb" />
                                <stop offset="100%" stopColor="#60a5fa" />
                            </linearGradient>

                            <linearGradient id="neutralGradient" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#475569" />
                                <stop offset="100%" stopColor="#94a3b8" />
                            </linearGradient>

                            <linearGradient id="greedGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#d97706" />
                                <stop offset="100%" stopColor="#f59e0b" />
                            </linearGradient>

                            <linearGradient id="extremeGreedGradient" x1="100%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor="#dc2626" />
                                <stop offset="100%" stopColor="#ef4444" />
                            </linearGradient>

                            <linearGradient id="needleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#ffffff" />
                                <stop offset="100%" stopColor={activeColor} />
                            </linearGradient>

                            {/* Define text paths for curved labels - 5 zones */}
                            <path id="pathExtFear" d="M 55 200 A 145 145 0 0 1 155 62" fill="none" />
                            <path id="pathFear" d="M 155 62 A 145 145 0 0 1 285 83" fill="none" />
                            <path id="pathNeutral" d="M 285 83 A 145 145 0 0 1 317 310" fill="none" />
                            <path id="pathGreed" d="M 317 310 A 145 145 0 0 1 110 338" fill="none" />
                            <path id="pathExtGreed" d="M 110 338 A 145 145 0 0 1 55 200" fill="none" />
                        </defs>

                        {/* Background Tracks */}
                        <circle cx="200" cy="200" r="140" fill="none" stroke="#1e293b" strokeWidth="2" opacity="0.5" />
                        <circle cx="200" cy="200" r="120" fill="none" stroke="#334155" strokeWidth="20" opacity="0.3" />

                        {/* Zone 1: Extreme Fear */}
                        <path d="M 80 200 A 120 120 0 0 1 163 86" fill="none" stroke="url(#extremeFearGradient)" strokeWidth={activeZone === 'extremeFear' ? "28" : "18"} strokeLinecap="round" opacity={activeZone === 'extremeFear' ? "1" : "0.3"} className="transition-all duration-500" />

                        {/* Zone 2: Fear */}
                        <path d="M 163 86 A 120 120 0 0 1 270 103" fill="none" stroke="url(#fearGradient)" strokeWidth={activeZone === 'fear' ? "28" : "18"} strokeLinecap="round" opacity={activeZone === 'fear' ? "1" : "0.3"} className="transition-all duration-500" />

                        {/* Zone 3: Neutral */}
                        <path d="M 270 103 A 120 120 0 0 1 297 291" fill="none" stroke="url(#neutralGradient)" strokeWidth={activeZone === 'neutral' ? "28" : "18"} strokeLinecap="round" opacity={activeZone === 'neutral' ? "1" : "0.3"} className="transition-all duration-500" />

                        {/* Zone 4: Greed */}
                        <path d="M 297 291 A 120 120 0 0 1 125 315" fill="none" stroke="url(#greedGradient)" strokeWidth={activeZone === 'greed' ? "28" : "18"} strokeLinecap="round" opacity={activeZone === 'greed' ? "1" : "0.3"} className="transition-all duration-500" />

                        {/* Zone 5: Extreme Greed */}
                        <path d="M 125 315 A 120 120 0 0 1 80 200" fill="none" stroke="url(#extremeGreedGradient)" strokeWidth={activeZone === 'extremeGreed' ? "28" : "18"} strokeLinecap="round" opacity={activeZone === 'extremeGreed' ? "1" : "0.3"} className="transition-all duration-500" />

                        {/* Hub & Arrow Pointer */}
                        <g style={{ transition: 'transform 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)' }} transform={`rotate(${angle} 200 200)`}>
                            <path d="M 195 200 L 200 60 L 205 200 Z" fill={activeColor} opacity="0.4" filter="url(#neon-glow)" />
                            <path d="M 195 200 L 200 60 L 205 200 Z" fill="url(#needleGradient)" stroke="#ffffff" strokeWidth="1" />
                            <circle cx="200" cy="200" r="8" fill="#0f172a" stroke={activeColor} strokeWidth="2" />
                            <circle cx="200" cy="200" r="4" fill={activeColor} className="animate-pulse" />
                        </g>

                        {/* Curved Zone Labels - 5 zones */}
                        <text fontSize="10" fontWeight="900" fill="#ffffff" letterSpacing="1" filter="url(#soft-glow)" opacity={activeZone === 'extremeFear' ? 1 : 0.7}>
                            <textPath href="#pathExtFear" startOffset="50%" textAnchor="middle">EXTREME FEAR</textPath>
                        </text>
                        <text fontSize="11" fontWeight="900" fill="#ffffff" letterSpacing="1" filter="url(#soft-glow)" opacity={activeZone === 'fear' ? 1 : 0.7}>
                            <textPath href="#pathFear" startOffset="50%" textAnchor="middle">FEAR</textPath>
                        </text>
                        <text fontSize="11" fontWeight="900" fill="#ffffff" letterSpacing="1" filter="url(#soft-glow)" opacity={activeZone === 'neutral' ? 1 : 0.7}>
                            <textPath href="#pathNeutral" startOffset="50%" textAnchor="middle">NEUTRAL</textPath>
                        </text>
                        <text fontSize="11" fontWeight="900" fill="#ffffff" letterSpacing="1" filter="url(#soft-glow)" opacity={activeZone === 'greed' ? 1 : 0.7}>
                            <textPath href="#pathGreed" startOffset="50%" textAnchor="middle">GREED</textPath>
                        </text>
                        <text fontSize="10" fontWeight="900" fill="#ffffff" letterSpacing="1" filter="url(#soft-glow)" opacity={activeZone === 'extremeGreed' ? 1 : 0.7}>
                            <textPath href="#pathExtGreed" startOffset="50%" textAnchor="middle">EXTREME GREED</textPath>
                        </text>
                    </svg>

                    {/* Dynamic Value Readout */}
                    <div className="absolute top-[50%] left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none mt-16">
                        <div
                            className="text-7xl font-black tabular-nums tracking-tighter drop-shadow-2xl transition-colors duration-500"
                            style={{
                                color: activeColor,
                                textShadow: `0 0 30px ${activeColor}40`
                            }}
                        >
                            {Math.round(value)}
                        </div>
                        <div
                            className="text-sm font-bold tracking-[0.4em] uppercase opacity-90 transition-colors duration-500 mt-2"
                            style={{ color: activeColor }}
                        >
                            {mmiData.label}
                        </div>
                    </div>
                </div>
            </div>
        </HUDCard>
    );
};

export default MarketMoodIndex;
