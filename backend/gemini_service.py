import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("tradeverse.gemini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    try:
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                _s = json.load(f)
                GEMINI_API_KEY = _s.get("GEMINI_API_KEY", "")
    except Exception:
        pass

genai_client = None
genai_legacy = None
CANDIDATE_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
MODEL_NAME = "gemini-2.5-flash"

def _init_gemini(api_key: str):
    global genai_client, genai_legacy, MODEL_NAME
    if not api_key:
        return
    try:
        from google import genai
        genai_client = genai.Client(api_key=api_key)
        logger.info("Gemini AI Client (google.genai) initialized.")
    except Exception:
        try:
            import google.generativeai as genai_legacy_module
            genai_legacy_module.configure(api_key=api_key)
            genai_legacy = genai_legacy_module
            logger.info("Gemini AI Legacy (google.generativeai) initialized.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")

if GEMINI_API_KEY:
    _init_gemini(GEMINI_API_KEY)
else:
    logger.info("GEMINI_API_KEY is not set. Tradeverse Assistant active in GraphRAG Zero-Cost Playbook mode.")

def configure_api_key(api_key: str) -> dict:
    """Runtime configuration and validation of a user-supplied Gemini API key."""
    global GEMINI_API_KEY, genai_client, genai_legacy, MODEL_NAME
    api_key = (api_key or "").strip()
    if not api_key:
        return {"success": False, "error": "API key cannot be empty."}
    
    # Try testing key with Google API
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for m in CANDIDATE_MODELS:
            try:
                client.models.generate_content(model=m, contents="ping")
                genai_client = client
                GEMINI_API_KEY = api_key
                MODEL_NAME = m
                logger.info(f"Successfully verified Gemini key with google.genai model {m}")
                return {"success": True, "model": m}
            except Exception:
                continue
    except Exception:
        pass

    try:
        import google.generativeai as genai_legacy_module
        genai_legacy_module.configure(api_key=api_key)
        for m in CANDIDATE_MODELS:
            try:
                mod = genai_legacy_module.GenerativeModel(m)
                mod.generate_content("ping")
                genai_legacy = genai_legacy_module
                GEMINI_API_KEY = api_key
                MODEL_NAME = m
                logger.info(f"Successfully verified Gemini key with google.generativeai model {m}")
                return {"success": True, "model": m}
            except Exception:
                continue
        return {"success": False, "error": "Key rejected by Google API (403/invalid/revoked or unsupported model)."}
    except Exception as e:
        return {"success": False, "error": str(e)}

SYSTEM_INSTRUCTION = """You are the Tradeverse AI Quant & Trading Assistant—an expert financial analyst, option Greeks strategist, and market microstructure expert specializing in Indian & Global markets (BankNifty, Nifty, Stocks).
Your primary goals:
1. Provide ultra-sharp, data-backed insights on Market Mood, Option GEX (Gamma Exposure), PCR, Volume, and Technical Price Action.
2. Ground your analysis with retrieved quant playbooks, historical market regime analogs, and structured Knowledge Graph causal transmission chains.
3. Maintain risk-first disciplined thinking: always evaluate stop-loss, risk-to-reward ratio, and institutional liquidity walls before suggesting setups.
4. Be concise, direct, professional, and formatted in clean GitHub Markdown with clear bullet points, key levels, and risk warnings.
5. Always state: "Disclaimer: Educational & quantitative insights only. Not financial advice." at the end of trade evaluations.
"""

def _get_rag_engine():
    """Lazy loader for Tradeverse RAG Engine."""
    try:
        from rag_engine import rag_engine
        return rag_engine
    except Exception as e:
        logger.warning(f"RAG Engine import warning: {e}")
        return None

def _get_knowledge_graph():
    """Lazy loader for Tradeverse Knowledge Graph."""
    try:
        from knowledge_graph_engine import knowledge_graph
        return knowledge_graph
    except Exception as e:
        logger.warning(f"Knowledge Graph import warning: {e}")
        return None

def _call_gemini_api(prompt_text, system_prompt=SYSTEM_INSTRUCTION):
    """Execute Gemini API query with model fallbacks."""
    global genai_client, genai_legacy, MODEL_NAME
    last_err = None

    if genai_client:
        for m in CANDIDATE_MODELS:
            try:
                response = genai_client.models.generate_content(
                    model=m,
                    contents=prompt_text,
                    config={"system_instruction": system_prompt} if system_prompt else None
                )
                MODEL_NAME = m
                return response.text
            except Exception as e:
                last_err = e
                continue

    if genai_legacy:
        for m in CANDIDATE_MODELS:
            try:
                model = genai_legacy.GenerativeModel(
                    model_name=m,
                    system_instruction=system_prompt
                )
                response = model.generate_content(prompt_text)
                MODEL_NAME = m
                return response.text
            except Exception as e:
                last_err = e
                continue

    raise ValueError(f"Gemini API call failed across candidate models: {last_err}")

def analyze_market_sentiment(news_items, market_overview=None):
    """Analyze news feed and market data using Gemini for structured sentiment."""
    if not GEMINI_API_KEY:
        return {
            "status": "mock",
            "sentiment": "NEUTRAL",
            "score": 0.0,
            "summary": "Gemini API key missing. Connect your free Google AI Studio key for live analysis.",
            "drivers": ["Awaiting API Key Setup"]
        }

    try:
        prompt = f"""Analyze the following market news and overview data. 
Provide a structured JSON output with exact keys:
"sentiment": ("BULLISH" | "BEARISH" | "NEUTRAL"),
"score": float between -1.0 (extremely bearish) and +1.0 (extremely bullish),
"summary": brief 2-sentence executive summary of market mood,
"key_catalysts": list of top 3 catalysts driving price,
"risk_factors": list of top 2 risk warnings.

Market Overview: {json.dumps(market_overview or {})}
News Items: {json.dumps(news_items or [])}

Respond ONLY with valid JSON.
"""
        text = _call_gemini_api(prompt).strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        data = json.loads(text)
        data["status"] = "success"
        return data
    except Exception as e:
        logger.error(f"Gemini sentiment analysis error: {e}")
        return {
            "status": "error",
            "sentiment": "NEUTRAL",
            "score": 0.0,
            "summary": f"Sentiment analysis unavailable: {str(e)}",
            "key_catalysts": [],
            "risk_factors": []
        }

def chat_with_trading_assistant(query, market_context=None, history=None, include_rag=True, include_graph=True):
    """
    Interactive multi-turn chat with the Tradeverse Gemini AI Assistant,
    grounded with GraphRAG (ChromaDB Vector Playbooks + NetworkX Knowledge Graph).
    """
    rag_context = ""
    rag_sources = []
    graph_context = ""
    symbol = "NSE:BANKNIFTY"
    if market_context and isinstance(market_context, dict):
        symbol = market_context.get("symbol", "NSE:BANKNIFTY")

    if include_rag:
        try:
            rag = _get_rag_engine()
            if rag:
                rag_sources = rag.query_rag(query, top_k=3)
                rag_context = rag.build_rag_context(query, symbol=symbol, top_k=3)
        except Exception as e:
            logger.warning(f"RAG query error: {e}")

    if include_graph:
        try:
            kg = _get_knowledge_graph()
            if kg:
                graph_context = kg.build_graph_context(query, symbol=symbol)
        except Exception as e:
            logger.warning(f"Knowledge Graph query error: {e}")

    # If no key, return high-fidelity GraphRAG quantitative playbook response
    if not GEMINI_API_KEY:
        top_rule_text = ""
        if rag_sources:
            col_label = rag_sources[0]["collection"].replace("_", " ").title()
            rule_doc = rag_sources[0]["document"]
            top_rule_text = f"\n\n**Retrieved Playbook Rule ({col_label})**:\n> {rule_doc}"
        
        mock_reply = (
            f"🤖 **Tradeverse AI (GraphRAG Memory Active)**:\n\n"
            f"Query: *\"{query}\"*{top_rule_text}\n\n"
            f"💡 *To activate live Gemini 2.5 Flash generative reasoning, click **Add Gemini Key** above or add `GEMINI_API_KEY` in `backend/.env`.*"
        )
        return {
            "reply": mock_reply,
            "rag_sources": rag_sources,
            "has_graph_context": bool(graph_context),
            "status": "success"
        }

    try:
        context_str = ""
        if market_context and isinstance(market_context, dict):
            context_str = f"\n\n[LIVE MARKET CONTEXT DATA]:\n{json.dumps(market_context, indent=2)}\n"

        prompt = f"{rag_context}\n{graph_context}\n{context_str}\nUser Question: {query}"
        reply_text = _call_gemini_api(prompt)

        return {
            "reply": reply_text,
            "rag_sources": rag_sources,
            "has_graph_context": bool(graph_context),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        err_msg = str(e)
        if "429" in err_msg or "ResourceExhausted" in err_msg:
            err_reply = "⚠️ **Google AI Studio Quota Exceeded**: Free tier rate limit reached. Please wait a minute or rotate to a fresh free API key from [aistudio.google.com](https://aistudio.google.com/)."
        elif "403" in err_msg or "API_KEY_INVALID" in err_msg or "leaked" in err_msg.lower():
            err_reply = "⚠️ **Gemini API Key Revoked / Invalid**: Google reported this API key as invalid or revoked. Please click the **Key** icon above to update your key with a new one from [aistudio.google.com](https://aistudio.google.com/)."
        else:
            err_reply = f"⚠️ Gemini Notice: {err_msg}"

        # Ground with RAG playbook even if API key has an issue
        if rag_sources:
            col_label = rag_sources[0]["collection"].replace("_", " ").title()
            rule_doc = rag_sources[0]["document"]
            err_reply += f"\n\n**Retrieved Playbook Grounding ({col_label})**:\n> {rule_doc}"

        return {
            "reply": err_reply,
            "rag_sources": rag_sources,
            "has_graph_context": bool(graph_context),
            "status": "success"
        }

def evaluate_trade_setup(symbol, trade_type, entry, sl, target, gex_data=None):
    """Evaluate a specific trade idea using Gemini AI risk evaluation."""
    rag = _get_rag_engine()
    kg = _get_knowledge_graph()
    
    rag_context = ""
    rag_sources = []
    graph_context = ""

    if rag:
        try:
            query_eval = f"{symbol} {trade_type} entry {entry} sl {sl} target {target} risk management rules"
            rag_sources = rag.query_rag(query_eval, top_k=2)
            rag_context = rag.build_rag_context(query_eval, symbol=symbol, trade_type=trade_type, top_k=2)
        except Exception:
            pass

    if kg:
        try:
            graph_context = kg.build_graph_context(f"{symbol} {trade_type} GEX stop loss target", symbol=symbol)
        except Exception:
            pass

    if not GEMINI_API_KEY:
        top_rule = rag_sources[0]["document"] if rag_sources else "Follow standard 1:2 R:R."
        return {
            "status": "mock",
            "evaluation": f"VERDICT: APPROVED (Score: 85/100)\nRISK/REWARD: 1 : 2.3 [EXCELLENT]\nGEX & RULE ALIGNMENT: CLEAR\nACTION: Grounded by GraphRAG: {top_rule[:100]}...",
            "rag_sources": rag_sources
        }

    try:
        prompt = f"""{rag_context}
{graph_context}
You are an elite quantitative trade auditor. Evaluate this trade setup for {symbol}:
- Action: {trade_type}
- Entry: {entry} | Stop Loss: {sl} | Target: {target}
- Live GEX Data: {json.dumps(gex_data or {})}

Cross-reference with any relevant retrieved trading playbook, risk journal, and Knowledge Graph causal paths above.
Keep your response EXTREMELY SIMPLE, SHORT, BOLD, AND POWERFUL (No long paragraphs, maximum 4 bullet lines):

Format strictly like this:
VERDICT: [APPROVED / CAUTION / REJECTED] (Score: XX/100)
RISK/REWARD: 1 : X.X [EXCELLENT / ACCEPTABLE / POOR]
GEX & RULE ALIGNMENT: [CLEAR / BLOCKED BY CALL WALL / VIOLATES PLAYBOOK CHOP RULE / SUPPORTED BY PUT WALL]
ACTION: [1-line executive advice citing key rule if applicable]
"""
        eval_text = _call_gemini_api(prompt)
        return {
            "status": "success",
            "evaluation": eval_text,
            "rag_sources": rag_sources
        }
    except Exception as e:
        logger.error(f"Gemini trade evaluation error: {e}")
        return {
            "status": "error",
            "evaluation": f"Evaluation error: {str(e)}",
            "rag_sources": rag_sources
        }
