import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const HUDCard = ({ children, className = "", title = "SYSTEM", neonColor = "indigo", lastUpdated = null }) => {
    const [timeDiff, setTimeDiff] = useState("SYNCING");

    useEffect(() => {
        if (!lastUpdated) return;

        const updateDiff = () => {
            const now = new Date();
            const past = new Date(lastUpdated);
            const diffMs = now - past;
            const diffSec = Math.floor(diffMs / 1000);

            if (diffSec < 2) setTimeDiff("JUST NOW");
            else if (diffSec < 60) setTimeDiff(`${diffSec}S AGO`);
            else setTimeDiff(`${Math.floor(diffSec / 60)}M AGO`);
        };

        updateDiff(); // Initial call
        const interval = setInterval(updateDiff, 1000);
        return () => clearInterval(interval);
    }, [lastUpdated]);

    return (
        <div className={`relative group ${className}`}>
            {/* Clipped Inner Container for Content & Background */}
            <div className="absolute inset-0 overflow-hidden rounded-2xl z-0">
                {/* Main Glass Panel */}
                <div className={`absolute inset-0 bg-${neonColor}-500/[0.04] backdrop-blur-xl border border-${neonColor}-500/25 rounded-2xl shadow-[0_0_15px_rgba(0,0,0,0.5)]`} />
            </div>

            {/* Corner Reticles (Fighter Jet HUD style) - Outside clip if needed, or inside. 
                They are inset-0, so they fit in the rounded box. Let's put them in the root to be safe or duplicate the inset logic.
                Actually, simpler: Just clip the content container? 
                The background glass is already rounded. 
                Let's apply overflow-hidden ONLY to the content container and maybe the background if needed.
                But the user said "datas are clashing", implying content spill.
            */}
            <div className="absolute inset-0 pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity duration-500 z-10 rounded-2xl overflow-hidden">
                {/* Top Left */}
                <svg className="absolute top-0 left-0 w-3 h-3 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M20 2 L2 2 L2 20" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Top Right */}
                <svg className="absolute top-0 right-0 w-3 h-3 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M0 2 L18 2 L18 20" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Bottom Left */}
                <svg className="absolute bottom-0 left-0 w-3 h-3 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M2 0 L2 18 L20 18" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Bottom Right */}
                <svg className="absolute bottom-0 right-0 w-3 h-3 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M0 18 L18 18 L18 0" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
            </div>


            {/* Label Tab - UNCLIPPED */}
            <div className={`absolute -top-2 left-3 px-1.5 bg-[#050507] border border-${neonColor}-500/50 text-[7px] font-black text-${neonColor}-400 tracking-widest uppercase rounded shadow-[0_0_10px_rgba(0,0,0,1)] z-30`}>
                {title}
            </div>

            {/* Timestamp Tab - UNCLIPPED */}
            {lastUpdated && (
                <div className={`absolute -bottom-1.5 right-3 px-1.5 bg-[#050507] border border-${neonColor}-500/30 text-[6px] font-mono text-${neonColor}-400/80 tracking-widest uppercase rounded z-30 flex items-center gap-1`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>UPD: {timeDiff}</span>
                </div>
            )}

            {/* Content Container - CLIPPED */}
            <div className="relative z-10 p-0.5 h-full overflow-hidden rounded-2xl">
                {children}
            </div>

            <style jsx>{`
                @keyframes scan {
                    0% { top: -10%; opacity: 0; }
                    10% { opacity: 1; }
                    90% { opacity: 1; }
                    100% { top: 110%; opacity: 0; }
                }
                .animate-scan {
                    animation: scan 4s linear infinite;
                }
            `}</style>
        </div>
    );
};

export default HUDCard;
