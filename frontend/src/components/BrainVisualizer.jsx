import React from 'react';
import ConfidenceGauge from './ConfidenceGauge';
import HUDCard from './ui/HUDCard';

/**
 * BrainVisualizer
 * Visualizes the agreement/intensity of the 5 key neural components.
 */
const BrainVisualizer = ({ scores = {}, className = "" }) => {
    // Scores are typically -1.0, 0.0, or 1.0 from the backend.
    // We treat absolute value as confidence/intensity for the circular gauge.
    const mapScore = (val) => Math.abs(val || 0);

    return (
        <HUDCard title="NEURAL CORE BRAIN" neonColor="cyan" className={`${className}`}>
            <div className="h-full w-full pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
                <div className="absolute -bottom-[20%] -left-[10%] w-[150px] h-[150px] bg-cyan-600/10 blur-[50px] rounded-full" />
            </div>

            <div className="relative grid grid-cols-2 md:grid-cols-5 gap-4 p-4 items-center justify-items-center">
                <div className="flex flex-col items-center">
                    <ConfidenceGauge
                        score={mapScore(scores.technical)}
                        label="DAILY"
                    />
                    <span className={`text-[8px] font-black mt-1 ${scores.technical > 0 ? 'text-emerald-400' : scores.technical < 0 ? 'text-red-400' : 'text-slate-500'}`}>
                        {scores.technical > 0 ? 'BULLISH' : scores.technical < 0 ? 'BEARISH' : 'NEUTRAL'}
                    </span>
                </div>

                <div className="flex flex-col items-center">
                    <ConfidenceGauge
                        score={mapScore(scores.tft)}
                        label="TEMPORAL"
                    />
                    <span className={`text-[8px] font-black mt-1 ${scores.tft > 0 ? 'text-emerald-400' : scores.tft < 0 ? 'text-red-400' : 'text-slate-500'}`}>
                        {scores.tft > 0 ? 'BULLISH' : scores.tft < 0 ? 'BEARISH' : 'NEUTRAL'}
                    </span>
                </div>

                <div className="flex flex-col items-center">
                    <ConfidenceGauge
                        score={mapScore(scores.rl)}
                        label="TIMING"
                    />
                    <span className={`text-[8px] font-black mt-1 ${scores.rl > 0 ? 'text-emerald-400' : scores.rl < 0 ? 'text-red-400' : 'text-slate-500'}`}>
                        {scores.rl > 0 ? 'BUY' : scores.rl < 0 ? 'SELL' : 'WAIT'}
                    </span>
                </div>

                <div className="flex flex-col items-center">
                    <ConfidenceGauge
                        score={mapScore(scores.sentiment)}
                        label="SENTIMENT"
                    />
                    <span className={`text-[8px] font-black mt-1 ${scores.sentiment > 0 ? 'text-emerald-400' : scores.sentiment < 0 ? 'text-red-400' : 'text-slate-500'}`}>
                        {scores.sentiment > 0.3 ? 'HOT' : scores.sentiment < -0.3 ? 'COLD' : 'LUKEWARM'}
                    </span>
                </div>

                <div className="flex flex-col items-center">
                    <ConfidenceGauge
                        score={mapScore(scores.options)}
                        label="OPTIONS"
                    />
                    <span className={`text-[8px] font-black mt-1 ${scores.options > 0 ? 'text-emerald-400' : scores.options < 0 ? 'text-red-400' : 'text-slate-500'}`}>
                        {scores.options > 0 ? 'LONG' : scores.options < 0 ? 'SHORT' : 'BALANCED'}
                    </span>
                </div>
            </div>

            <div className="px-6 pb-4 border-t border-white/5 pt-3">
                <div className="flex justify-between items-center">
                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">Convergence Protocol</span>
                    <span className="text-[10px] text-cyan-400 font-mono font-bold">ALPHA-7 ACTIVE</span>
                </div>
            </div>
        </HUDCard>
    );
};

export default BrainVisualizer;
