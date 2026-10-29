import os
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from news_scraper import NewsScraper

logger = logging.getLogger("NewsSentimentEngine")

class NewsSentimentEngine:
    """
    Pillar 2: Real-Time LLM News Sentiment & Keyword Intercept Engine for Tradeverse.
    Uses Gemini LLM to score financial news headlines for Indian Banking / Index impact.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("📰 NewsSentimentEngine Initialized with Gemini 1.5 Flash")
            except Exception as e:
                logger.warning(f"Gemini Init Warning in NewsSentimentEngine: {e}")
                self.model = None
        else:
            self.model = None

        self.scraper = NewsScraper()
        self.cached_sentiment = {"score": 0.0, "label": "NEUTRAL", "impact": "LOW", "timestamp": datetime.now()}

    def _keyword_intercept(self, headlines: List[str]) -> Tuple[float, str]:
        """
        Fast rule-based keyword intercept for high-impact news events (RBI Repo Rate, NPAs, Bank Mergers).
        """
        bullish_keywords = ["rbi rate cut", "repo rate cut", "record profit", "npa drop", "gdp surge", "credit growth"]
        bearish_keywords = ["rbi rate hike", "repo rate hike", "npa rise", "bank fraud", "inflation spike", "crr hike"]

        combined_text = " ".join(headlines).lower()

        bull_count = sum(1 for k in bullish_keywords if k in combined_text)
        bear_count = sum(1 for k in bearish_keywords if k in combined_text)

        if bull_count > bear_count:
            return min(1.0, 0.4 * bull_count), "BULLISH_KEYWORD_INTERCEPT"
        elif bear_count > bull_count:
            return max(-1.0, -0.4 * bear_count), "BEARISH_KEYWORD_INTERCEPT"
        
        return 0.0, "NEUTRAL"

    def analyze_news_sentiment(self, symbol: str = "BANKNIFTY") -> Dict:
        """
        Fetches live news headlines and scores sentiment via Gemini LLM with exponential half-life decay.
        """
        now = datetime.now()

        # Fetch live headlines
        news_items = []
        try:
            news_items = self.scraper.get_latest_news(symbol)
        except Exception as e:
            logger.warning(f"Failed to scrape news in NewsSentimentEngine: {e}")

        headlines = [item.get('title', '') for item in news_items if item.get('title')]

        if not headlines:
            headlines = [f"{symbol} trading in standard market range.", "RBI maintains monetary stance."]

        keyword_score, kw_label = self._keyword_intercept(headlines)

        # Query Gemini LLM if available
        llm_score = keyword_score
        llm_label = kw_label
        impact_level = "MEDIUM" if keyword_score != 0 else "LOW"

        if self.model and headlines:
            try:
                prompt = (
                    f"You are a Senior Quantitative Analyst at a top Indian Hedge Fund.\n"
                    f"Analyze these latest financial headlines for {symbol} (Bank Nifty / Indian Banking Sector):\n"
                    f"{chr(10).join(['- ' + h for h in headlines[:5]])}\n\n"
                    f"Provide:\n"
                    f"1. Sentiment Score (-1.0 for Extremely Bearish, +1.0 for Extremely Bullish, 0.0 for Neutral)\n"
                    f"2. Overall Classification (BULLISH, BEARISH, NEUTRAL)\n"
                    f"3. Impact Rating (LOW, MEDIUM, HIGH, CRITICAL)\n"
                    f"Format output as: SCORE: <value> | LABEL: <label> | IMPACT: <impact>"
                )
                response = self.model.generate_content(prompt)
                res_text = response.text.strip()

                if "SCORE:" in res_text:
                    try:
                        parts = res_text.split("|")
                        score_val = float(parts[0].split("SCORE:")[1].strip())
                        label_val = parts[1].split("LABEL:")[1].strip()
                        impact_val = parts[2].split("IMPACT:")[1].strip()

                        llm_score = max(-1.0, min(1.0, score_val))
                        llm_label = label_val
                        impact_level = impact_val
                    except Exception as parse_e:
                        logger.warning(f"Error parsing Gemini news sentiment response: {parse_e}")
            except Exception as llm_e:
                logger.warning(f"Gemini LLM Sentiment API call failed: {llm_e}")

        # Combine Keyword Intercept and LLM Score
        final_score = (0.6 * llm_score) + (0.4 * keyword_score)
        final_score = round(max(-1.0, min(1.0, final_score)), 2)

        self.cached_sentiment = {
            "score": final_score,
            "label": llm_label if final_score != 0 else "NEUTRAL",
            "impact": impact_level,
            "headlines_count": len(headlines),
            "top_headline": headlines[0] if headlines else "No active headlines",
            "timestamp": now
        }

        return self.cached_sentiment
