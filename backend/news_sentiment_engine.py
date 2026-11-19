import os
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from news_scraper import NewsScraper

logger = logging.getLogger("NewsSentimentEngine")

class NewsSentimentEngine:
    """
    Pillar 2: Real-Time Financial News & Social Media Sentiment Analysis Engine for Tradeverse.
    
    Dual-Core Architecture:
    1. Primary/Augmented: Gemini 3.5 Flash-Lite LLM for deep contextual sentiment reasoning.
    2. Zero-Cost Fallback: Rule-Based Dalal Street Financial & Retail Sentiment Lexicon
       that operates at zero cost and zero latency, guaranteeing 100% uptime even during
       Google AI Studio free-tier rate limits or HTTP 429 quota exhaustion.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = None
        self.model_name = "lexicon_fallback"

        if self.api_key and self.api_key != "MOCK_KEY":
            try:
                from gemini_service import ModelRouter
                self.model, self.model_name = ModelRouter.get_sentiment_model(self.api_key)
                logger.info(f"📰 NewsSentimentEngine Initialized via ModelRouter with {self.model_name}")
            except Exception as e:
                logger.warning(f"Gemini Init Warning in NewsSentimentEngine: {e}")
                self.model = None

        self.scraper = NewsScraper()
        self.cached_sentiment: Dict[str, Dict] = {}

        # Comprehensive Dalal Street Financial & Retail Trader Sentiment Lexicon
        self.bullish_lexicon = {
            "record high": 1.5,
            "52-week high": 1.5,
            "all-time high": 1.5,
            "bulls take charge": 1.4,
            "bull run": 1.3,
            "short squeeze": 1.3,
            "strong buying": 1.2,
            "fii inflows": 1.2,
            "fii buying": 1.2,
            "dii buying": 1.0,
            "rate cut": 1.4,
            "repo rate cut": 1.5,
            "record profit": 1.2,
            "profit jumps": 1.1,
            "surge": 0.8,
            "rallies": 0.8,
            "rally": 0.8,
            "breakout": 1.0,
            "npa drop": 1.1,
            "credit growth": 1.0,
            "gdp surge": 1.2,
            "upgrade": 0.9,
            "outperform": 0.9,
            "target raised": 0.9,
            "gain": 0.5,
            "jump": 0.6,
            "optimistic": 0.7
        }

        self.bearish_lexicon = {
            "bloodbath": 1.5,
            "crash": 1.5,
            "meltdown": 1.4,
            "plunge": 1.3,
            "margin call": 1.4,
            "fii dump": 1.3,
            "fii selling": 1.2,
            "fii outflow": 1.2,
            "rate hike": 1.4,
            "repo rate hike": 1.5,
            "crr hike": 1.3,
            "inflation spike": 1.2,
            "war risk": 1.3,
            "npa rise": 1.2,
            "bank fraud": 1.5,
            "sebi notice": 1.2,
            "penalty": 1.0,
            "downgrade": 1.0,
            "profit booking": 0.8,
            "breakdown": 1.1,
            "bearish grip": 1.2,
            "selloff": 1.0,
            "slump": 0.9,
            "dive": 0.8,
            "tumble": 0.8,
            "drop": 0.5,
            "fall": 0.5,
            "loss": 0.6
        }

        self.neutral_keywords = [
            "rangebound", "consolidation", "flat", "cautious", "mixed", "hurdle", 
            "wait and watch", "sideways", "eyes global cues", "muted"
        ]

    def _score_with_lexicon(self, headlines: List[str]) -> Tuple[float, str, str]:
        """
        Calculates normalized sentiment score (-1.0 to +1.0) and impact level using the financial lexicon.
        """
        if not headlines:
            return 0.0, "NEUTRAL", "LOW"

        bull_points = 0.0
        bear_points = 0.0
        neutral_matches = 0

        combined = " ".join(headlines).lower()

        for term, weight in self.bullish_lexicon.items():
            if term in combined:
                bull_points += weight * combined.count(term)

        for term, weight in self.bearish_lexicon.items():
            if term in combined:
                bear_points += weight * combined.count(term)

        for term in self.neutral_keywords:
            if term in combined:
                neutral_matches += 1

        total_points = bull_points + bear_points
        if total_points == 0.0:
            return 0.0, "NEUTRAL", "LOW"

        # Normalized Polarity: -1.0 to +1.0
        raw_score = (bull_points - bear_points) / (total_points + (0.5 * neutral_matches))
        final_score = round(max(-1.0, min(1.0, raw_score)), 3)

        if final_score >= 0.25:
            label = "BULLISH"
        elif final_score <= -0.25:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        if total_points >= 4.0:
            impact = "HIGH"
        elif total_points >= 2.0:
            impact = "MEDIUM"
        else:
            impact = "LOW"

        return final_score, label, impact

    def analyze_news_sentiment(self, symbol: str = "BANKNIFTY") -> Dict:
        """
        Fetches live multi-source headlines and scores sentiment with Gemini LLM + Financial Lexicon.
        """
        now = datetime.now()
        clean_symbol = symbol.replace("^", "").replace(".NS", "").upper()

        # Check in-memory cache (valid for 3 minutes to avoid thrashing)
        cached = self.cached_sentiment.get(clean_symbol)
        if cached and (now - cached.get("timestamp", now)).total_seconds() < 180:
            return cached

        # 1. Fetch live RSS headlines
        news_items = []
        try:
            news_items = self.scraper.fetch_latest_news(clean_symbol)
        except Exception as e:
            logger.warning(f"News scraping warning for {clean_symbol}: {e}")

        headlines = [item.get("title", "") for item in news_items if item.get("title")]
        if not headlines:
            headlines = [f"{clean_symbol} trading within expected volatility boundaries."]

        # 2. Compute baseline score using the Dalal Street Financial Lexicon
        lex_score, lex_label, lex_impact = self._score_with_lexicon(headlines)

        final_score = lex_score
        final_label = lex_label
        final_impact = lex_impact
        engine_used = "FINANCIAL_LEXICON_ENGINE"

        # 3. Augment with Gemini LLM if available and active
        if self.model:
            try:
                top_sample = chr(10).join([f"- {h}" for h in headlines[:6]])
                prompt = (
                    f"You are a Senior Quantitative Sentiment Analyst at an Indian F&O hedge fund.\n"
                    f"Analyze these live financial headlines for {clean_symbol} (NSE India):\n"
                    f"{top_sample}\n\n"
                    f"Evaluate both institutional news and retail trader sentiment.\n"
                    f"Respond strictly in this format:\n"
                    f"SCORE: <float between -1.0 and 1.0> | LABEL: <BULLISH/BEARISH/NEUTRAL> | IMPACT: <LOW/MEDIUM/HIGH>"
                )
                response = self.model.generate_content(prompt)
                res_text = response.text.strip().upper()

                if "SCORE:" in res_text:
                    parts = res_text.split("|")
                    llm_score = float(parts[0].split("SCORE:")[1].strip())
                    llm_label = parts[1].split("LABEL:")[1].strip()
                    llm_impact = parts[2].split("IMPACT:")[1].strip()

                    # Blend: 60% LLM + 40% Lexical
                    blended = (0.6 * llm_score) + (0.4 * lex_score)
                    final_score = round(max(-1.0, min(1.0, blended)), 3)
                    final_label = llm_label if abs(final_score) >= 0.20 else "NEUTRAL"
                    final_impact = llm_impact
                    engine_used = f"HYBRID_LLM_{self.model_name}"
            except Exception as llm_err:
                logger.info(f"Gemini LLM paused ({llm_err}). Engaged zero-cost Financial Lexicon Engine (Score: {lex_score}, {lex_label}).")
                engine_used = "ZERO_COST_DALAL_STREET_LEXICON"

        result = {
            "symbol": clean_symbol,
            "sentiment_score": final_score,
            "sentiment_label": final_label,
            "impact": final_impact,
            "engine": engine_used,
            "headlines_count": len(headlines),
            "top_headline": headlines[0] if headlines else "No active headlines",
            "sample_headlines": headlines[:4],
            "news_context": news_items[:8],
            "timestamp": now
        }

        self.cached_sentiment[clean_symbol] = result
        return result

    def analyze_sentiment(self, symbol: str = "BANKNIFTY") -> Dict:
        """Alias for analyze_news_sentiment."""
        return self.analyze_news_sentiment(symbol)

if __name__ == "__main__":
    engine = NewsSentimentEngine()
    for test_sym in ["BANKNIFTY", "NIFTY"]:
        res = engine.analyze_news_sentiment(test_sym)
        print(f"\n--- {test_sym} Sentiment ---")
        print(f"Score: {res['sentiment_score']:+.3f} | Label: {res['sentiment_label']} | Impact: {res['impact']}")
        print(f"Engine: {res['engine']} | Headlines: {res['headlines_count']}")
        print(f"Top: {res['top_headline']}")
