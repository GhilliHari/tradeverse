import operator
import importlib.metadata
# Polyfill for Python 3.9 compatibility
if not hasattr(importlib.metadata, 'packages_distributions'):
    importlib.metadata.packages_distributions = lambda: {}
import numpy as np
from typing import Annotated, List, Dict, Optional, Any
import pandas as pd
from typing_extensions import TypedDict
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
import google.generativeai as genai
import os
from news_scraper import NewsScraper
# Imports moved inside class for lazy loading
# from broker_factory import get_broker_client
# from risk_engine import RiskEngine
# from model_engine import ModelEngine
# TFTEngine and RLTradingAgent are imported lazily inside __init__
# from data_pipeline import DataPipeline
import logging

logger = logging.getLogger(__name__)

# Define the State for our Intelligence Graph
class AgentState(TypedDict):
    symbol: str
    news_context: List[Dict]
    technical_context: Dict
    sentiment_analysis: Annotated[str, operator.add]
    sentiment_label: str # POSITIVE, NEGATIVE, NEUTRAL
    technical_analysis: Annotated[str, operator.add]
    pcr: float
    oi_change: float
    ai_prediction: str # UP, DOWN
    tft_prediction: str # UP, DOWN
    rl_action: int # 0: Hold, 1: Buy, 2: Sell
    sentiment_score: float # -1.0 to 1.0
    risk_approval: bool
    final_signal: str
    confidence: float
    regime: str
    trade_recommendation: Dict # { instrument, action, strike, option_type, reasoning, exit_plan }
    model_scores: Dict # Raw component scores (technical, tft, rl, sentiment, options)
    positions: List[Dict] # Current open positions for monitoring
    exit_signals: List[Dict] # Recommendations for exiting active trades
    custom_df: Any # For offline backtesting

from token_manager import TokenManager
from config import config


class IntelligenceLayer:
    """
    LangGraph-based Committee of Agents logic for Tradeverse.
    """
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.scraper = NewsScraper()
        
        # Core flags and status
        self._kite = None
        self._risk_engine = None
        self._model_engine = None
        self._tft_engine = None
        self._rl_agent = None
        self.features = []
        
        # COR Upgrade Components (Weeks 4-6) - Lazy Loaded
        self._causality_engine = None
        self._regime_engine = None
        self._feature_optimizer = None
        self._stability_filters = None
        
        # Structural Alpha Components (Week 10) - Lazy Loaded
        self._component_tracker = None
        self._gex_engine = None
        self._meta_labeler = None
        
        self.workflow = self._create_workflow()
        self.token_manager = TokenManager()
        
        logger.info("⚡ IntelligenceLayer Initialized (LITE/Lazy Mode)")

    @property
    def kite(self):
        if self._kite is None:
            try:
                from broker_factory import get_broker_client
                self._kite = get_broker_client()
            except Exception as e:
                logger.error(f"Lazy Load Kite Failed: {e}")
        return self._kite

    @property
    def risk_engine(self):
        if self._risk_engine is None:
            try:
                from risk_engine import RiskEngine
                self._risk_engine = RiskEngine()
            except Exception as e:
                logger.error(f"Lazy Load RiskEngine Failed: {e}")
        return self._risk_engine

    @property
    def model_engine(self):
        if self._model_engine is None:
            try:
                from model_engine import ModelEngine
                self._model_engine = ModelEngine()
                self.features = self._model_engine.features
                logger.info("✅ Classic AI Engine Loaded")
            except Exception as e:
                logger.error(f"Lazy Load ModelEngine Failed: {e}")
        return self._model_engine

    @property
    def tft_engine(self):
        if self._tft_engine is None and self.features:
            try:
                from tft_engine import TFTEngine
                self._tft_engine = TFTEngine(self.features)
                self._tft_engine.load_model()
                logger.info("✅ TFT Engine Loaded")
            except Exception as e:
                logger.error(f"Lazy Load TFTEngine Failed: {e}")
        return self._tft_engine

    @property
    def rl_agent(self):
        if self._rl_agent is None and self.features:
            try:
                from rl_trading_agent import RLTradingAgent
                self._rl_agent = RLTradingAgent(None, self.features)
                self._rl_agent.load_model()
                logger.info("✅ RL agent Loaded")
            except Exception as e:
                logger.error(f"Lazy Load RL agent Failed: {e}")
        return self._rl_agent

    @property
    def causality_engine(self):
        if self._causality_engine is None:
            try:
                from causality_engine import BankNiftyCausalityEngine
                self._causality_engine = BankNiftyCausalityEngine()
            except: pass
        return self._causality_engine

    @property
    def regime_engine(self):
        if self._regime_engine is None:
            try:
                from regime_engine import IntradayRegimeEngine
                self._regime_engine = IntradayRegimeEngine()
                self._regime_engine.load_model()
            except: pass
        return self._regime_engine

    @property
    def feature_optimizer(self):
        if self._feature_optimizer is None:
            try:
                from feature_optimizer import FeatureOptimizer
                self._feature_optimizer = FeatureOptimizer()
            except: pass
        return self._feature_optimizer

    @property
    def stability_filters(self):
        if self._stability_filters is None:
            try:
                from stability_filters import StabilityFilters
                self._stability_filters = StabilityFilters()
            except: pass
        return self._stability_filters

    @property
    def component_tracker(self):
        if self._component_tracker is None:
            try:
                from component_causality import ComponentTracker
                self._component_tracker = ComponentTracker(self.kite)
            except: pass
        return self._component_tracker

    @property
    def gex_engine(self):
        if self._gex_engine is None:
            try:
                from gex_engine import GEXEngine
                self._gex_engine = GEXEngine()
            except: pass
        return self._gex_engine

    @property
    def meta_labeler(self):
        if self._meta_labeler is None:
            try:
                from meta_labeler import MetaLabeler
                self._meta_labeler = MetaLabeler()
            except: pass
        return self._meta_labeler

        self.workflow = self._create_workflow()
        self.token_manager = TokenManager() # Initialize Token Manager

    def _sentiment_agent(self, state: AgentState):
        """Analyzes market sentiment from news."""
        news = self.scraper.fetch_latest_news(state['symbol'])
        prompt = f"Analyze the sentiment for {state['symbol']} based on these headlines: {news}.\n" \
                 f"1. Is the overall sentiment POSITIVE, NEGATIVE, or NEUTRAL?\n" \
                 f"2. Provide a brief reason.\n" \
                 f"Format: SENTIMENT: [Label], REASON: [Text]"
        
        try:
            # Capture usage metadata implies a valid response object
            response = self.model.generate_content(prompt)
            res_text = response.text.upper()
            
            # Record Token Usage
            if response.usage_metadata:
                self.token_manager.add_usage(
                    model_name="gemini-2.5-flash",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count
                )
        except Exception as e:
            logger.error(f"Sentiment Analysis Failed: {e}")
            res_text = "SENTIMENT: NEUTRAL, REASON: Model unavailable/Error."
        
        label = "NEUTRAL"
        score = 0.0
        if "POSITIVE" in res_text: 
            label = "POSITIVE"
            score = 0.75 # Default quantized positive
        elif "NEGATIVE" in res_text: 
            label = "NEGATIVE"
            score = -0.75 # Default quantized negative
        
        return {"sentiment_analysis": res_text, "sentiment_label": label, "sentiment_score": score, "news_context": news}

    def _options_agent(self, state: AgentState):
        """Analyzes Put-Call Ratio and Open Interest for institutional bias."""
        # In a real scenario, this would fetch from a broker's option chain
        # For Bank Nifty, PCR > 1.2 is often Overbought (reversal), PCR < 0.7 is Oversold.
        # Here we simulate based on the committee context or fetch if available.
        pcr = 1.0 # Default Neutral
        oi_change = 0.0
        
        if self.kite:
            chain = self.kite.get_option_chain(state['symbol'])
            total_ce_oi = sum(s.get('oi_ce', 0) for s in chain)
            total_pe_oi = sum(s.get('oi_pe', 0) for s in chain)
            if total_ce_oi > 0:
                pcr = total_pe_oi / total_ce_oi
            
            # Use GEX Engine for deep mapping
            if self.gex_engine:
                 spot = state.get('technical_context', {}).get('ltp', 50000)
                 gex_res = self.gex_engine.analyze_chain(chain, spot)
                 analysis = f"Options Matrix: PCR={pcr:.2f}. " \
                            f"Call Wall: {gex_res.get('call_wall')}, Put Wall: {gex_res.get('put_wall')}, " \
                            f"Max Pain: {gex_res.get('max_pain')}."
                 return {"pcr": pcr, "oi_change": oi_change, "technical_analysis": state['technical_analysis'] + " " + analysis, "gex_data": gex_res}
        
        analysis = f"Options Matrix: PCR={pcr:.2f}. Institutional bias is {'BULLISH' if pcr < 0.9 else 'BEARISH' if pcr > 1.1 else 'NEUTRAL'}."
        return {"pcr": pcr, "oi_change": oi_change, "technical_analysis": state['technical_analysis'] + " " + analysis}

    def _technical_agent(self, state: AgentState):
        """Analyzes technical data using the trained 12-year AI Model."""
        # Normalize symbol for pipeline if it's Nifty Bank
        symbol = "^NSEBANK" if "BANK" in state['symbol'].upper() else state['symbol']
        
        prediction_str = "UNKNOWN"
        conviction = "LOW"
        prob = 0.5
        is_ood = False
        
        prediction_str = "UNKNOWN"
        conviction = "LOW"
        prob = 0.5
        is_ood = False
        regime = "NOMINAL"
        
        try:
            from data_pipeline import DataPipeline
            pipeline = DataPipeline(symbol)
            pipeline.raw_data = pd.DataFrame() # Defensive init
            pipeline.cleaned_data = pd.DataFrame() 
            
            # Priority: Use custom_df if provided (Backtest Mode)
            success = False
            if state.get('custom_df') is not None:
                pipeline.cleaned_data = state['custom_df'].copy()
                pipeline.raw_data = pipeline.cleaned_data # Ensure raw_data is available for causality
                success = True
            
            # Priority: Use Broker data if LIVE, fallback to yfinance
            elif config.ENV == "LIVE" and self.kite and hasattr(self.kite, 'is_connected') and self.kite.is_connected():
                logger.info("Intelligence Layer fetching live data via Broker...")
                # For live inference, we need enough buffer for 200-period indicators
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7) 
                success = pipeline.fetch_live_data_broker(self.kite, start_date, end_date)
            
            if not success:
                logger.info("Intelligence Layer falling back to yfinance data...")
                # run_full_pipeline already handles the logic internally
                success = pipeline.run_full_pipeline()

            if success:
                # --- NEW COR UPGRADE PIPELINE ---
                
                # 1. Apply Stability Filtering (Kalman) to close prices
                if self.stability_filters and not pipeline.cleaned_data.empty:
                    # Smoothing price action for better signal detection
                    pipeline.cleaned_data['Close_Smoothed'] = self.stability_filters.apply_kalman_filter(pipeline.cleaned_data['Close'])
                
                # 2. Detect Current Regime
                current_regime = "NOMINAL"
                if self.regime_engine and not pipeline.cleaned_data.empty:
                    # In true live mode, we'd ensure it's fitted. 
                    # Assuming pre-loaded or fit-on-fly capability.
                    current_regime = self.regime_engine.classify_regime(datetime.now(), pipeline.cleaned_data.iloc[-1])
                
                # 3. Detect Causal Strength (Futures/VIX lead signals)
                causal_strength = 0.5
                causal_factors = []
                if self.causality_engine and not pipeline.raw_data.empty:
                     causal_res = self.causality_engine.detect_causal_relationships(pipeline.raw_data)
                     causal_strength = causal_res.get('overall_causal_strength', 0.5)
                     causal_factors = self.causality_engine.get_causal_factors()

                # --- NEW: Component Alpha (Phase 5) ---
                component_data = {"score": 0, "status": "NEUTRAL"}
                if self.component_tracker:
                     # Fetch prices first (uses mock broker if in backtest)
                     self.component_tracker.fetch_live_data() 
                     component_data = self.component_tracker.calculate_component_score()
                     logger.info(f"Component Alpha: Score={component_data['score']}, Status={component_data['status']}")

                # 4. Model Prediction
                features = pipeline.cleaned_data.iloc[-1:]
                pred_data = {}
                if self.model_engine and not features.empty:
                    # Confidence scoring uses causal factor + regime boost
                    pred_data = self.model_engine.predict_with_confidence(features, regime=current_regime, causal_strength=causal_strength)
                    
                    if pred_data:
                        prediction_str = "UP" if pred_data['prediction'] == 1 else "DOWN"
                        conviction = pred_data.get('conviction', 'LOW')
                        prob = pred_data.get('probability', 0.5)
                        is_ood = pred_data.get('is_ood', False)
                        regime = pred_data.get('regime_provided', current_regime)
                        confidence = pred_data.get('confidence', 0.0)
                else:
                    regime = "LITE_MODE"
                    confidence = 0.0
                    
        except Exception as e:
            logger.error(f"Technical Agent Error: {e}")
        
        # Get current LTP
        price_data = self.kite.ltp(state['symbol']) if self.kite else {}
        ltp = price_data.get(state['symbol'], {}).get('last_price', 0)
        
        regime = pred_data.get('regime_provided', 'NOMINAL') if success and pred_data else 'NOMINAL'
        confidence = pred_data.get('confidence', 0.0) if success and pred_data else 0.0
        
        analysis = f"COR Augmented Engine: Pred={prediction_str}, Conf={confidence:.1f}%, Regime={regime}, Causal={causal_strength:.2f}."
        if is_ood: analysis += " [OOD WARNING]"
        
        # Capture levels and additional metrics for frontend
        levels = pred_data.get('levels', {}) if success and pred_data else {}
        atr = pred_data.get('atr', 0) if success and pred_data else 0
        rsi = pipeline.cleaned_data['RSI'].iloc[-1] if success and not pipeline.cleaned_data.empty and 'RSI' in pipeline.cleaned_data else 50

        return {
            "technical_analysis": analysis, 
            "ai_prediction": prediction_str, 
            "regime": regime,
            "confidence": confidence,
            "technical_context": {
                "ltp": ltp, 
                "conviction": conviction, 
                "prob": prob, 
                "is_ood": is_ood, 
                "regime": regime,
                "confidence": confidence,
                "causal_strength": causal_strength,
                "causal_factors": causal_factors,
                "component_alpha": component_data, # NEW Week 10
                "levels": levels,
                "atr": atr,
                "rsi": rsi
            }
        }

    def _tft_agent(self, state: AgentState):
        """Deep Temporal Context Analysis using TFT."""
        # For simplicity in this demo, we assume the pipeline in state or re-fetch
        # In production, we'd pass the normalized sequence through
        try:
            from data_pipeline import DataPipeline
            pipeline = DataPipeline(state['symbol'])
            pipeline.run_full_pipeline()
        except: return {"tft_prediction": "NEUTRAL"}
        
        tft_pred = "NEUTRAL"
        if self.tft_engine and pipeline.cleaned_data is not None and len(pipeline.cleaned_data) >= 30:
            recent = pipeline.cleaned_data.tail(30)
            prob = self.tft_engine.predict(recent)
            tft_pred = "UP" if prob > 0.55 else "DOWN" if prob < 0.45 else "NEUTRAL"
        
        return {"tft_prediction": tft_pred, "technical_analysis": state['technical_analysis'] + f" [TFT Context: {tft_pred}]"}

    def _rl_sniper(self, state: AgentState):
        """Reinforcement Learning Sniper node for entry/exit timing."""
        # RL expects the full feature vector as observation
        # We simulate the latest observation state
        # In a real loop, this would be the actual live feed data
        try:
             from data_pipeline import DataPipeline
             pipeline = DataPipeline(state['symbol'])
             pipeline.run_full_pipeline()
        except: return {"rl_action": 0}
        
        rl_action = 0
        if self.rl_agent and self.model_engine and pipeline.cleaned_data is not None and not pipeline.cleaned_data.empty:
            latest_row = pipeline.cleaned_data.tail(1)
            # Reconstruct the observation exactly as the environment does
            obs = latest_row[self.model_engine.features].values[0]
            # normalized_balance=1.0, position=0 (Guest assume flat)
            obs = np.append(obs, [1.0, 0.0]).astype(np.float32)
            rl_action = self.rl_agent.get_action(obs)
            
        return {"rl_action": rl_action}

    def _risk_auditor(self, state: AgentState):
        """Validates if the signal is safe."""
        risk_check = self.risk_engine.get_risk_status()
        is_safe = risk_check['circuit_breaker_status'] == "NOMINAL"
        return {"risk_approval": is_safe}
    def _aggregator(self, state: AgentState):
        """
        Consolidates signals from all agents using a Convergence Score.
        """
        greedy = state.get('greedy', False)
        regime = state.get('regime', 'NOMINAL')
        tech_pred = state['ai_prediction']
        tft_pred = state.get('tft_prediction', 'NEUTRAL')
        rl_action = state.get('rl_action', 0)
        sent_score = state.get('sentiment_score', 0.0)
        pcr = state.get('pcr', 1.0)
        risk_safe = state['risk_approval']

        from strategy_optimizer import StrategyOptimizer
        
        # 1. Convergence Scoring
        sig_data = {
            "tech_pred": tech_pred,
            "tft_pred": tft_pred,
            "rl_action": rl_action,
            "sentiment_score": sent_score,
            "pcr": pcr
        }
        convergence_score, component_scores = StrategyOptimizer.calculate_convergence_score(sig_data)
        
        # Dynamic Signal Generation based on Convergence
        final_signal = "HOLD"
        confidence = state.get('confidence', 0.0)
        reasoning = ""
        
        # NOMINAL/RANGE_BOUND/TRENDING: needs |0.3|, VOLATILE: |0.5|, CRASH/OOD: |0.7|
        req_score = 0.7 # Default strict
        
        if regime in ["NOMINAL", "RANGE_BOUND", "TRENDING_INTRADAY", "POWER_HOUR_TREND", "LUNCH_LULL"]:
            req_score = 0.3
        elif regime in ["VOLATILE", "OPENING_VOLATILITY"]:
            req_score = 0.5
            
        if greedy:
            req_score = 0.1 # Very low threshold for simulation density
            
        if abs(convergence_score) >= req_score and risk_safe:
            # --- NEW: Phase 5 Meta-Labeling Gate ---
            current_confidence = state.get('confidence', 0.0)
            tech_ctx = state.get('technical_context', {})
            component_alpha = tech_ctx.get('component_alpha', {})
            gex_data = state.get('gex_data', {})
            
            raw_signal = "BUY" if convergence_score > 0 else "SELL"
            
            # Meta-labeling vetting
            vetted_signal = raw_signal
            success_prob = 1.0 # Default if meta-labeler fails
            
            if self.meta_labeler and not greedy:
                vetted_signal, success_prob = self.meta_labeler.get_vetted_signal(
                    raw_signal, 
                    current_confidence, 
                    tech_ctx, 
                    component_alpha, 
                    gex_data,
                    threshold=0.65 # Institutional Grade threshold
                )

            # --- NEW: GEX Safety Gate (Week 10) ---
            gex_gate = {"allow": True, "reason": "Path clear"}
            if self.gex_engine:
                 ltp = tech_ctx.get('ltp', 0)
                 gex_gate = self.gex_engine.get_safety_gate(vetted_signal, ltp)

            if vetted_signal != "HOLD" and gex_gate['allow']:
                final_signal = vetted_signal
                confidence = current_confidence
                reasoning = f"Vetted Alpha: Success Prob {success_prob:.2f} | Confidence {current_confidence:.1f}%"
            else:
                final_signal = "HOLD"
                confidence = current_confidence 
                if vetted_signal == "HOLD":
                    reasoning = f"Signal Refused (Meta-Labeler): Prob {success_prob:.2f} below threshold."
                elif not gex_gate['allow']:
                    reasoning = f"GEX Block: {gex_gate['reason']}"
                else:
                    reasoning = f"Signal Gated: Convergence/Risk check failed."
        
        # 2. Exit Plan Generation (Targets & SL)
        ltp = state['technical_context'].get('ltp', 0)
        atr = state['technical_context'].get('atr', ltp * 0.01) # Default 1% ATR
        
        exit_plan = {}
        if final_signal != "HOLD":
            # Dynamic targets based on regime and GEX walls
            targets = StrategyOptimizer.calculate_targets(ltp, final_signal, atr, regime=regime, gex_data=gex_data)
            
            # Dynamic SL based on regime
            sl_price = StrategyOptimizer.calculate_tsl(ltp, ltp, final_signal, atr, regime=regime)
            
            exit_plan = {
                "initial_sl": sl_price,
                "trailing_sl_active": True,
                "targets": targets
            }

        # Strike Selection...
        strike = round(ltp / 100) * 100
        option_type = "CE" if final_signal == "BUY" else "PE" if final_signal == "SELL" else "N/A"
        instrument = f"{state['symbol'].replace('^', '')} {strike} {option_type}" if final_signal != "HOLD" else "WAITING FOR SIGNAL"
        
        # Append regime info to reasoning if not already there
        reasoning += f" | Regime: {regime} (Convergence: {convergence_score:.2f} vs Req: {req_score})"
        if not risk_safe: reasoning = "Trade Blocked by Risk Engine."

        return {
            "final_signal": final_signal, 
            "confidence": confidence,
            "model_scores": component_scores,
            "trade_recommendation": {
                "instrument": instrument,
                "action": final_signal,
                "strike": strike if final_signal != "HOLD" else 0,
                "option_type": option_type,
                "reasoning": reasoning,
                "exit_plan": exit_plan
            }
        }

    def _exit_monitor(self, state: AgentState):
        """
        Monitors open positions for exit signals (TSL hit, Target hit, Regime flip).
        """
        from strategy_optimizer import StrategyOptimizer
        positions = state.get('positions', [])
        ltp = state['technical_context'].get('ltp', 0)
        atr = state['technical_context'].get('atr', ltp * 0.01)
        regime = state.get('regime', 'NOMINAL')
        
        exit_recommendations = []
        logger.info(f"Exit Monitor: Checking {len(positions)} positions at LTP {ltp}...")
        
        for pos in positions:
            side = pos.get('side')
            entry = pos.get('entry_price')
            current_sl = pos.get('stop_loss')
            
            # 1. Update/Check Trailing Stop
            new_tsl = StrategyOptimizer.calculate_tsl(entry, ltp, side, atr)
            
            should_exit = False
            reason = ""
            
            if side == "BUY":
                if ltp <= current_sl:
                    should_exit = True
                    reason = f"Stop Loss Hit (LTP {ltp} <= SL {current_sl})"
                elif regime == "CRASH":
                    should_exit = True
                    reason = "Regime Flip: CRASH detected"
            else: # SELL
                if ltp >= current_sl:
                    should_exit = True
                    reason = f"Stop Loss Hit (LTP {ltp} >= SL {current_sl})"
                elif regime == "NOMINAL" and ltp < entry: # Exit if Sell in bullish flip
                    pass # logic...
                    
            if should_exit:
                logger.warning(f"🚨 EXIT SIGNAL: {pos['instrument']} - {reason}")
                exit_recommendations.append({"instrument": pos['instrument'], "reason": reason})
        
        return {"exit_signals": exit_recommendations}

    def _create_workflow(self):
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("sentiment", self._sentiment_agent)
        workflow.add_node("technical", self._technical_agent)
        workflow.add_node("options", self._options_agent)
        workflow.add_node("tft", self._tft_agent)
        workflow.add_node("rl_sniper", self._rl_sniper)
        workflow.add_node("risk", self._risk_auditor)
        workflow.add_node("exit_monitor", self._exit_monitor)
        workflow.add_node("aggregator", self._aggregator)

        # entry point starts parallel execution of data-gathering agents
        # actually, langgraph entry point is usually a single node. 
        # I'll create a 'coordinator' node that branches out.
        def _coordinator(state: AgentState):
            return state
        
        workflow.add_node("coordinator", _coordinator)
        workflow.set_entry_point("coordinator")
        
        # Parallel branches
        workflow.add_edge("coordinator", "sentiment")
        workflow.add_edge("coordinator", "technical")
        workflow.add_edge("coordinator", "options")
        
        # Sequential dependencies (if any, but let's try to keep them mostly parallel)
        # Technical results might be needed by TFT/RL
        workflow.add_edge("technical", "tft")
        workflow.add_edge("technical", "rl_sniper")
        
        # Converge at Risk Auditor
        workflow.add_edge("sentiment", "risk")
        workflow.add_edge("options", "risk")
        workflow.add_edge("tft", "risk")
        workflow.add_edge("rl_sniper", "risk")
        
        # Risk feeds into Aggregator and Exit Monitor
        workflow.add_edge("risk", "aggregator")
        workflow.add_edge("risk", "exit_monitor")
        
        workflow.add_edge("aggregator", END)
        workflow.add_edge("exit_monitor", END)

        return workflow.compile()

    def run_analysis(self, symbol: str, positions: List[Dict] = [], custom_df=None, greedy: bool = False):
        """Starts the agentic committee analysis process."""
        initial_state = {
            "symbol": symbol,
            "positions": positions,
            "custom_df": custom_df,
            "greedy": greedy,
            "exit_signals": [],
            "news_context": [],
            "technical_context": {},
            "sentiment_analysis": "",
            "sentiment_label": "NEUTRAL",
            "technical_analysis": "",
            "ai_prediction": "UNKNOWN",
            "risk_approval": False,
            "final_signal": "HOLD",
            "confidence": 0.0,
            "model_scores": {},
            "regime": "NOMINAL"
        }
        return self.workflow.invoke(initial_state)

if __name__ == "__main__":
    # Test (requires GEMINI_API_KEY in env)
    api_key = os.getenv("GEMINI_API_KEY", "MOCK_KEY")
    intel = IntelligenceLayer(api_key)
    result = intel.run_analysis("^NSEBANK")
    print(f"Final Signal: {result['final_signal']} (Conf: {result['confidence']})")
    print(f"Details: {result['sentiment_label']} | Conviction: {result['technical_context'].get('conviction')}")
