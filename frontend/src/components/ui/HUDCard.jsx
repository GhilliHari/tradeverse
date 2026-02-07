import React from 'react';
import { motion } from 'framer-motion';

const HUDCard = ({ children, className = "", title = "SYSTEM", neonColor = "indigo" }) => {
    // Generate random ID for unique mask/gradient refs if needed

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
                <svg className="absolute top-0 left-0 w-5 h-5 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M20 2 L2 2 L2 20" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Top Right */}
                <svg className="absolute top-0 right-0 w-5 h-5 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M0 2 L18 2 L18 20" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Bottom Left */}
                <svg className="absolute bottom-0 left-0 w-5 h-5 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M2 0 L2 18 L20 18" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
                {/* Bottom Right */}
                <svg className="absolute bottom-0 right-0 w-5 h-5 text-indigo-400" viewBox="0 0 20 20">
                    <path d="M0 18 L18 18 L18 0" fill="none" stroke={`var(--neon-${neonColor}, #6366f1)`} strokeWidth="2.5" strokeLinecap="square" />
                </svg>
            </div>


            {/* Label Tab - UNCLIPPED */}
            <div className={`absolute -top-3 left-4 px-2 py-0.5 bg-[#050507] border border-${neonColor}-500/50 text-[9px] font-black text-${neonColor}-400 tracking-widest uppercase rounded shadow-[0_0_10px_rgba(0,0,0,1)] z-30`}>
                {title}
            </div>

            {/* Content Container - CLIPPED */}
            <div className="relative z-10 p-1 h-full overflow-hidden rounded-2xl">
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
