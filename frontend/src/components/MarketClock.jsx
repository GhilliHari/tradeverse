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

        // If today is a weekend or it's already past 9:15 AM, move to future
        if (istDate.getDay() === 0) { // Sunday
            nextOpen.setDate(istDate.getDate() + 1);
        } else if (istDate.getDay() === 6) { // Saturday
            nextOpen.setDate(istDate.getDate() + 2);
        } else if (currentTotalMinutes >= marketOpenMinutes) {
            // Already past open today, move to tomorrow
            nextOpen.setDate(istDate.getDate() + 1);
            // If tomorrow is Saturday, move to Monday
            if (nextOpen.getDay() === 6) nextOpen.setDate(nextOpen.getDate() + 2);
        }

        return nextOpen;
    };

    const getMarketSession = () => {
        const istDate = getISTTime();
        const hours = istDate.getHours();
        const minutes = istDate.getMinutes();
        const day = istDate.getDay();

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

        if (day === 0 || day === 6) {
            sessionLabel = 'MARKET CLOSED';
            color = 'text-amber-500';
            dot = 'bg-amber-500';
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
            sessionLabel = `OPEN IN: ${countdownStr}`;
        }

        return { label: sessionLabel, color, dot, pulse };
    };

    const session = getMarketSession();

    // Override logic if backend explicitly says isOpen is true
    const effectiveLabel = (isOpen && !session.label.includes('OPEN IN')) ? 'MARKET OPEN' : session.label;
    const effectiveColor = (isOpen && !session.label.includes('OPEN IN')) ? 'text-emerald-500' : session.color;
    const effectiveDot = (isOpen && !session.label.includes('OPEN IN')) ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : session.dot;
    const effectivePulse = isOpen ? false : session.pulse;

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
        </div>
    );
};

export default MarketClock;
