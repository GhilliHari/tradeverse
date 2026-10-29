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
        <div className="flex items-center gap-1.5 px-1.5 py-0.5 h-[28px] rounded-lg bg-white/5 border border-white/[0.03] backdrop-blur-sm">
            <div className="relative flex items-center justify-center shrink-0">
                <div className={`w-1.5 h-1.5 rounded-full ${activeColor.bg} ${pulse ? 'animate-pulse' : ''} ${activeColor.shadow}`} />
                {pulse && (
                    <motion.div
                        animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                        className={`absolute w-1.5 h-1.5 rounded-full ${activeColor.bg}`}
                    />
                )}
            </div>
            <div className="flex flex-col leading-none min-w-0">
                <span className="text-[6px] font-black text-slate-500 uppercase tracking-tighter truncate">{label}</span>
                <span className={`text-[7px] font-black ${activeColor.text} tracking-wider truncate`}>{status}</span>
            </div>
        </div>
    );
};

export default StatusBadge;
