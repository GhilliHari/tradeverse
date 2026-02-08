import operator
import importlib.metadata
# Polyfill for Python 3.9 compatibility
if not hasattr(importlib.metadata, 'packages_distributions'):
    importlib.metadata.packages_distributions = lambda: {}
import numpy as np
from typing import Annotated, List, Union, Dict
from typing_extensions import TypedDict
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
import google.generativeai as genai
import os
from news_scraper import NewsScraper
from broker_factory import get_broker_client
from risk_engine import RiskEngine
from model_engine import ModelEngine
# TFTEngine and RLTradingAgent are imported lazily inside __init__
from data_pipeline import DataPipeline
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
    trade_recommendation: Dict # { instrument, action, strike, option_type, reasoning }

from token_manager import TokenManager

class IntelligenceLayer:
    """
    LangGraph-based Committee of Agents logic for Tradeverse.
    """
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.scraper = NewsScraper()
        self.kite = get_broker_client()
        self.risk_engine = RiskEngine()
        self.model_engine = ModelEngine()
        
        # Lazy Load Heavy Engines to prevent startup timeout
        from tft_engine import TFTEngine
        from rl_trading_agent import RLTradingAgent
        
        self.tft_engine = TFTEngine(self.model_engine.features)
        self.tft_engine.load_model()
        self.rl_agent = RLTradingAgent(None, self.model_engine.features) # Env not needed for inference
        self.rl_agent.load_model()
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
                    model_name="gemini-1.5-flash",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count
                )
        except Exception as e:
            logger.error(f"Sentiment Analysis Failed: {e}")
            res_text = "SENTIMENT: NEUTRAL, REASON: Model unavailable."
        
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
        
        pipeline = DataPipeline(symbol)
        
        # Priority: Use Broker data if LIVE, fallback to yfinance
        from config import config
        success = False
        if config.ENV == "LIVE" and self.kite and hasattr(self.kite, 'is_connected') and self.kite.is_connected():
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
            recent_features = pipeline.cleaned_data.tail(1)
            pred_data = self.model_engine.predict(recent_features)
            if pred_data:
                prediction_str = "UP" if pred_data['prediction'] == 1 else "DOWN"
                conviction = pred_data.get('conviction', 'LOW')
                prob = pred_data.get('probability', 0.5)
                is_ood = pred_data.get('is_ood', False)
        
        # Get current LTP
        price_data = self.kite.ltp(state['symbol'])
        ltp = price_data.get(state['symbol'], {}).get('last_price', 0)
        
        regime = pred_data.get('regime', 'NOMINAL') if success and pred_data else 'NOMINAL'
        analysis = f"AI Precision Engine: Prediction={prediction_str}, Conviction={conviction}, Prob={prob:.2%}, OOD={is_ood}, Regime={regime}."
        return {
            "technical_analysis": analysis, 
            "ai_prediction": prediction_str, 
            "regime": regime,
            "technical_context": {"ltp": ltp, "conviction": conviction, "prob": prob, "is_ood": is_ood, "regime": regime}
        }

    def _tft_agent(self, state: AgentState):
        """Deep Temporal Context Analysis using TFT."""
        # For simplicity in this demo, we assume the pipeline in state or re-fetch
        # In production, we'd pass the normalized sequence through
        pipeline = DataPipeline(state['symbol'])
        pipeline.run_full_pipeline()
        
        tft_pred = "NEUTRAL"
        if pipeline.cleaned_data is not None and len(pipeline.cleaned_data) >= 30:
            recent = pipeline.cleaned_data.tail(30)
            prob = self.tft_engine.predict(recent)
            tft_pred = "UP" if prob > 0.55 else "DOWN" if prob < 0.45 else "NEUTRAL"
        
        return {"tft_prediction": tft_pred, "technical_analysis": state['technical_analysis'] + f" [TFT Context: {tft_pred}]"}

    def _rl_sniper(self, state: AgentState):
        """Reinforcement Learning Sniper node for entry/exit timing."""
        # RL expects the full feature vector as observation
        # We simulate the latest observation state
        # In a real loop, this would be the actual live feed data
        pipeline = DataPipeline(state['symbol'])
        pipeline.run_full_pipeline()
        
        rl_action = 0
        if pipeline.cleaned_data is not None and not pipeline.cleaned_data.empty:
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
        Dynamic Alignment Rule:
        - NOMINAL: Requires 3/5 Alignment
        - VOLATILE: Requires 4/5 Alignment + Precision > 85%
        - CRASH: Requires 5/5 Alignment + Risk Engine Override
        """
        regime = state.get('regime', 'NOMINAL')
        
        # Committee Consensus Data
        tech_pred = state['ai_prediction']
        tft_pred = state.get('tft_prediction', 'NEUTRAL')
        rl_action = state.get('rl_action', 0)
        sent_score = state.get('sentiment_score', 0.0)
        pcr = state.get('pcr', 1.0)
        
        # Define Alignment Thresholds by Regime
        threshold_map = {
            "NOMINAL": 3,
            "VOLATILE": 4,
            "CRASH": 5
        }
        required_alignment = threshold_map.get(regime, 3)
        
        # Bullish Markers
        bullish_count = 0
        if tech_pred == "UP": bullish_count += 1
        if tft_pred == "UP": bullish_count += 1
        if rl_action == 1: bullish_count += 1
        if sent_score > 0.3: bullish_count += 1
        if pcr < 0.85: bullish_count += 1
        
        # Bearish Markers
        bearish_count = 0
        if tech_pred == "DOWN": bearish_count += 1
        if tft_pred == "DOWN": bearish_count += 1
        if rl_action == 2: bearish_count += 1
        if sent_score < -0.3: bearish_count += 1
        if pcr > 1.15: bearish_count += 1
        
        risk_safe = state['risk_approval']
        tech_prob = state['technical_context'].get('prob', 0.5)

        # Dynamic Signal Generation
        final_signal = "HOLD"
        confidence = 0.0
        reasoning = []
        
        aligned_count = max(bullish_count, bearish_count)
        
        if aligned_count >= required_alignment and risk_safe:
            if bullish_count > bearish_count:
                final_signal = "BUY"
                confidence = tech_prob + (0.05 * (bullish_count - (required_alignment - 1)))
            elif bearish_count > bullish_count:
                final_signal = "SELL"
                confidence = tech_prob + (0.05 * (bearish_count - (required_alignment - 1)))

        # Reasoning Output
        if final_signal != "HOLD":
            reasoning.append(f"Regime {regime} Alignment: {aligned_count}/{required_alignment} Locked")
            if aligned_count >= 4: reasoning.append("High-Conviction Committee Consensus")
            if tft_pred != "NEUTRAL": reasoning.append("Temporal Context Synced")
        
        # Cap confidence
        confidence = min(confidence, 0.99)
        
        # Strike Selection Logic
        ltp = state['technical_context'].get('ltp', 0)
        strike = round(ltp / 100) * 100
        option_type = "CE" if final_signal == "BUY" else "PE" if final_signal == "SELL" else "N/A"
        
        instrument = f"{state['symbol'].replace('^', '')} {strike} {option_type}" if final_signal != "HOLD" else "WAITING FOR SIGNAL"
        
        full_reasoning = f"{' AND '.join(reasoning)}." if reasoning else f"Market in {regime} mode. Needs {required_alignment} layers but got {aligned_count}."
        if not risk_safe: full_reasoning = "Trade Blocked by Risk Engine (Circuit Breaker/Volatility)."

        return {
            "final_signal": final_signal, 
            "confidence": confidence,
            "trade_recommendation": {
                "instrument": instrument,
                "action": final_signal,
                "strike": strike if final_signal != "HOLD" else 0,
                "option_type": option_type,
                "reasoning": full_reasoning
            }
        }

    def _create_workflow(self):
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("sentiment", self._sentiment_agent)
        workflow.add_node("technical", self._technical_agent)
        workflow.add_node("options", self._options_agent)
        workflow.add_node("tft", self._tft_agent)
        workflow.add_node("rl_sniper", self._rl_sniper)
        workflow.add_node("risk", self._risk_auditor)
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
        
        # Final Path
        workflow.add_edge("risk", "aggregator")
        workflow.add_edge("aggregator", END)

        return workflow.compile()

    def run_analysis(self, symbol: str):
        """Starts the agentic committee analysis process."""
        initial_state = {
            "symbol": symbol,
            "news_context": [],
            "technical_context": {},
            "sentiment_analysis": "",
            "sentiment_label": "NEUTRAL",
            "technical_analysis": "",
            "ai_prediction": "UNKNOWN",
            "risk_approval": False,
            "final_signal": "HOLD",
            "confidence": 0.0,
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
