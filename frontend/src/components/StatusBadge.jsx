import React from 'react';
import { motion } from 'framer-motion';

const StatusBadge = ({ label, status, pulse = false, color = 'emerald' }) => {

    const colorMap = {
        emerald: { bg: 'bg-emerald-500', text: 'text-emerald-500', shadow: 'shadow-[0_0_8px_#10b981]' },
        red: { bg: 'bg-red-500', text: 'text-red-500', shadow: 'shadow-[0_0_8px_#ef4444]' },
        indigo: { bg: 'bg-indigo-500', text: 'text-indigo-500', shadow: 'shadow-[0_0_8px_#6366f1]' },
        amber: { bg: 'bg-amber-500', text: 'text-amber-500', shadow: 'shadow-[0_0_8px_#f59e0b]' },
        slate: { bg: 'bg-slate-500', text: 'text-slate-500', shadow: 'shadow-[0_0_8px_#64748b]' },
    };

    const activeColor = colorMap[color] || colorMap.slate;

    return (
        <div className="flex items-center gap-2 px-3 py-1.5 h-[38px] rounded-full bg-white/5 border border-white/5 backdrop-blur-sm">
            <div className="relative flex items-center justify-center">
                <div className={`w-2 h-2 rounded-full ${activeColor.bg} ${pulse ? 'animate-pulse' : ''} ${activeColor.shadow}`} />
                {pulse && (
                    <motion.div
                        animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                        className={`absolute w-2 h-2 rounded-full ${activeColor.bg}`}
                    />
                )}
            </div>
            <div className="flex flex-col leading-none">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{label}</span>
                <span className={`text-[10px] font-black ${activeColor.text} tracking-wider`}>{status}</span>
            </div>
        </div>
    );
};

export default StatusBadge;
