import React from 'react';
import { motion } from 'framer-motion';

const ConfidenceGauge = ({ score, label = "AI CONFIDENCE" }) => {
    // Score is 0.0 to 1.0
    const percentage = Math.min(Math.max(score * 100, 0), 100);
    const radius = 30;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    // Determine color based on score
    let color = '#64748b'; // slate
    if (percentage > 70) color = '#10b981'; // emerald
    else if (percentage > 40) color = '#f59e0b'; // amber
    else if (percentage > 0) color = '#ef4444'; // red

    return (
        <div className="flex flex-col items-center">
            <div className="relative w-20 h-20 flex items-center justify-center">
                {/* Background Circle */}
                <svg className="w-full h-full transform -rotate-90">
                    <circle
                        cx="40"
                        cy="40"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="6"
                        fill="transparent"
                        className="text-slate-800"
                    />
                    {/* Foreground Circle */}
                    <motion.circle
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        cx="40"
                        cy="40"
                        r={radius}
                        stroke={color}
                        strokeWidth="6"
                        fill="transparent"
                        strokeDasharray={circumference}
                        strokeLinecap="round"
                        className="drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]"
                    />
                </svg>
                <div className="absolute flex flex-col items-center">
                    <span className="text-sm font-black text-white">{Math.round(percentage)}%</span>
                </div>
            </div>
            <span className="text-[10px] font-bold text-slate-500 tracking-widest mt-1">{label}</span>
        </div>
    );
};

export default ConfidenceGauge;
