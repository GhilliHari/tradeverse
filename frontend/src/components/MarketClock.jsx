import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

const MarketClock = ({ isOpen }) => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

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

    const getISTTime = () => {
        return new Date(time.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    };

    const getISTTimeString = () => {
        return time.toLocaleTimeString('en-IN', {
            timeZone: 'Asia/Kolkata',
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const getNextMarketOpen = (istDate) => {
        const nextOpen = new Date(istDate);
        nextOpen.setHours(9, 15, 0, 0);

        const currentTotalMinutes = istDate.getHours() * 60 + istDate.getMinutes();
        const marketOpenMinutes = 9 * 60 + 15;

        // Find nearest working day
        let found = false;
        let checkDate = new Date(istDate);

        // If it's already past 9:15 AM today, start checking from tomorrow
        if (currentTotalMinutes >= marketOpenMinutes) {
            checkDate.setDate(checkDate.getDate() + 1);
        }

        let safety = 0;
        while (!found && safety < 10) {
            const checkDay = checkDate.getDay();
            const checkDateStr = `${checkDate.getFullYear()}-${String(checkDate.getMonth() + 1).padStart(2, '0')}-${String(checkDate.getDate()).padStart(2, '0')}`;
            if (checkDay !== 0 && checkDay !== 6 && !holidays.includes(checkDateStr)) {
                found = true;
                nextOpen.setFullYear(checkDate.getFullYear());
                nextOpen.setMonth(checkDate.getMonth());
                nextOpen.setDate(checkDate.getDate());
            } else {
                checkDate.setDate(checkDate.getDate() + 1);
            }
            safety++;
        }

        return nextOpen;
    };

    const getMarketSession = () => {
        const istDate = getISTTime();
        const hours = istDate.getHours();
        const minutes = istDate.getMinutes();
        const day = istDate.getDay();
        const localDate = `${istDate.getFullYear()}-${String(istDate.getMonth() + 1).padStart(2, '0')}-${String(istDate.getDate()).padStart(2, '0')}`;
        const isHoliday = holidays.includes(localDate);

        const totalMinutes = hours * 60 + minutes;

        const preMarketLiveOpen = 9 * 60;     // 9:00 AM
        const marketOpen = 9 * 60 + 15;        // 9:15 AM
        const closingSoonStart = 15 * 60 + 15; // 3:15 PM
        const marketClose = 15 * 60 + 30;      // 3:30 PM

        let sessionLabel = '';
        let color = '';
        let dot = '';
        let pulse = false;
        let showCountdown = false;

        if (day === 0 || day === 6 || isHoliday) {
            sessionLabel = isHoliday ? 'MARKET HOLIDAY' : 'MARKET CLOSED';
            color = 'text-amber-500';
            dot = 'bg-amber-500 shadow-[0_0_8px_#f59e0b]';
            showCountdown = true;
        } else if (totalMinutes >= preMarketLiveOpen && totalMinutes < marketOpen) {
            sessionLabel = 'OPENING SOON';
            color = 'text-indigo-400';
            dot = 'bg-indigo-400 shadow-[0_0_10px_#818cf8]';
            pulse = true;
        } else if (totalMinutes >= marketOpen && totalMinutes < closingSoonStart) {
            sessionLabel = 'LIVE MARKET';
            color = 'text-emerald-500';
            dot = 'bg-emerald-500 shadow-[0_0_8px_#10b981]';
        } else if (totalMinutes >= closingSoonStart && totalMinutes < marketClose) {
            sessionLabel = 'CLOSING SOON';
            color = 'text-rose-500';
            dot = 'bg-rose-500 shadow-[0_0_12px_#f43f5e]';
            pulse = true;
        } else {
            sessionLabel = totalMinutes < preMarketLiveOpen ? 'PRE-MARKET EARLY' : 'POST-MARKET';
            color = 'text-slate-500';
            dot = 'bg-slate-500';
            showCountdown = true;
        }

        if (showCountdown) {
            const nextOpen = getNextMarketOpen(istDate);
            const diffMs = nextOpen - istDate;
            const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
            const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);

            const countdownStr = `${String(diffHrs).padStart(2, '0')}:${String(diffMins).padStart(2, '0')}:${String(diffSecs).padStart(2, '0')}`;
            if (isHoliday) {
                // Keep the label as HOLIDAY but show countdown if needed elsewhere or just keep label
            } else {
                sessionLabel = `OPEN IN: ${countdownStr}`;
            }
        }

        return { label: sessionLabel, color, dot, pulse };
    };

    const getExpiryInfo = () => {
        const istDate = getISTTime();
        const day = istDate.getDay();
        const totalMinutes = istDate.getHours() * 60 + istDate.getMinutes();
        const isMarketHours = totalMinutes >= 555 && totalMinutes < 930; // 9:15 to 3:30
        const localDate = `${istDate.getFullYear()}-${String(istDate.getMonth() + 1).padStart(2, '0')}-${String(istDate.getDate()).padStart(2, '0')}`;
        const isHoliday = holidays.includes(localDate);

        if (!isMarketHours || isHoliday) return null;

        switch (day) {
            case 0: return null; // Sunday
            case 1: return { name: "MIDCAP", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" };
            case 2: return { name: "FINNIFTY", color: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/20" };
            case 3: return { name: "BANKNIFTY", color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" };
            case 4: return { name: "NIFTY 50", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" };
            default: return null;
        }
    };

    const session = getMarketSession();
    const expiry = getExpiryInfo();

    // Override logic if backend explicitly says isOpen is true
    const isActuallyOpen = isOpen && !session.label.includes('MARKET HOLIDAY') && !session.label.includes('MARKET CLOSED');
    const effectiveLabel = (isActuallyOpen) ? 'MARKET OPEN' : session.label;
    const effectiveColor = (isActuallyOpen) ? 'text-emerald-500' : session.color;
    const effectiveDot = (isActuallyOpen) ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : session.dot;
    const effectivePulse = isActuallyOpen ? false : session.pulse;

    return (
        <div className={`flex items-center gap-3 px-4 py-1.5 bg-white/5 border rounded-2xl backdrop-blur-md group hover:bg-white/10 transition-all duration-300 h-[38px] ${effectivePulse ? 'border-indigo-500/30' : 'border-white/10'}`}>
            <div className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${effectiveDot} ${effectivePulse ? 'animate-ping' : ''} transition-all duration-500`} />
                <div className="flex flex-col">
                    <span className={`text-[11px] font-black uppercase tracking-wider ${effectiveColor} leading-none ${effectivePulse ? 'animate-pulse' : ''} whitespace-nowrap`}>
                        {effectiveLabel}
                    </span>
                    <span className="text-[7px] font-black tracking-widest text-slate-400 font-mono mt-0.5 opacity-80 whitespace-nowrap">
                        {getISTTimeString()} <span className="text-[6px] opacity-40">IST</span>
                    </span>
                </div>
            </div>
            <div className="h-4 w-px bg-white/10 mx-1" />
            <div className="flex items-center justify-center p-1.5 bg-indigo-500/10 rounded-lg group-hover:bg-indigo-500/20 transition-colors">
                <Clock className={`w-3 h-3 text-indigo-400 ${effectivePulse ? 'animate-spin-slow' : ''}`} />
            </div>
            {expiry && (
                <>
                    <div className="h-4 w-px bg-white/10 mx-1" />
                    <div className={`${expiry.bg} ${expiry.border} border px-2 py-0.5 rounded-full flex items-center gap-1.5 animate-pulse`}>
                        <div className={`w-1 h-1 rounded-full ${expiry.color.replace('text', 'bg')} shadow-[0_0_8px_currentColor]`} />
                        <span className={`text-[8px] font-black uppercase tracking-[0.1em] ${expiry.color}`}>
                            {expiry.name} EXPIRY
                        </span>
                    </div>
                </>
            )}
        </div>
    );
};

export default MarketClock;
