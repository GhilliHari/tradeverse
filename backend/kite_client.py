
import logging
from config import config
from mock_kite import MockKiteConnect

logger = logging.getLogger("KiteClient")

class LiveKiteConnect:
    def __init__(self, api_key, access_token):
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            logger.error("kiteconnect library not installed. Please run `pip install kiteconnect`.")
            raise

        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        logger.info("Initialized Live KiteConnect Client")

    def ltp(self, instrument_token):
        """
        Fetches LTP from Zerodha.
        """
        try:
            # kite.ltp returns { "NSE:INFY": { "instrument_token": 123, "last_price": 1234.5 } }
            return self.kite.ltp(instrument_token)
        except Exception as e:
            logger.error(f"Error fetching LTP for {instrument_token}: {e}")
            return {}

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, validity=None, tag=None):
        try:
            return self.kite.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                validity=validity,
                tag=tag
            )
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    def profile(self):
        """
        Returns profile info from Zerodha.
        """
        try:
            p = self.kite.profile()
            return {
                "user_id": p.get("user_id", "N/A"),
                "user_name": p.get("user_name", "Zerodha User"),
                "email": p.get("email", "N/A"),
                "broker": "ZERODHA",
                "status": "LIVE"
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha profile: {e}")
            return {"user_id": "ERROR", "user_name": "Profile Error", "broker": "ZERODHA", "status": "EXCEPTION"}

    def get_option_chain(self, symbol="NSE:BANKNIFTY"):
        """
        Constructs an option chain for the live market.
        Note: Real-time option chain construction requires complex symbol mapping.
        This MVP version fetches the real Spot Price and then constructs a 
        synchetic chain structure (similar to Mock) but anchored to the REAL market price.
        To support real premiums, we would need to fetch quotes for specific NFO symbols.
        """
        try:
            # 1. Fetch Real Spot Price
            ltp_data = self.ltp(symbol)
            if symbol not in ltp_data:
                return []
            
            spot = ltp_data[symbol]['last_price']
            
            # 2. Generate Strikes based on Real Spot
            # (Note: For full live premiums, we would need a Symbol Mapper here)
            base_strike = round(spot / 100) * 100
            strikes = []
            
            # Heuristic calculation for MVP live view (since we don't have NFO symbol mapping db here)
            # This allows the UI to populate with valid Strike Prices even if premiums are estimated
            import random 
            for i in range(-5, 6):
                strike_price = base_strike + (i * 100)
                dist = abs(spot - strike_price)
                # Intrinsic value + Time value approximation
                ce_premium = max(10, (spot - strike_price) + (200 - dist * 0.5)) if spot > strike_price else max(10, (200 - dist * 0.5))
                pe_premium = max(10, (strike_price - spot) + (200 - dist * 0.5)) if spot < strike_price else max(10, (200 - dist * 0.5))
                
                strikes.append({
                    "strike": strike_price,
                    "ce_premium": round(ce_premium, 2), # Estimated
                    "pe_premium": round(pe_premium, 2), # Estimated
                    "oi_ce": 0, # Requires rigorous NFO lookup
                    "oi_pe": 0  # Requires rigorous NFO lookup
                })
            return strikes

        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return []

def get_kite_client():
    if config.ENV == "LIVE":
        if not config.KITE_API_KEY or not config.KITE_ACCESS_TOKEN:
             logger.warning("LIVE mode requested but API keys missing. Falling back to MOCK.")
             return MockKiteConnect(api_key="MOCK_KEY")
        
        logger.info("Connecting to LIVE Zerodha Environment...")
        return LiveKiteConnect(api_key=config.KITE_API_KEY, access_token=config.KITE_ACCESS_TOKEN)
    else:
        logger.info("Using MOCK Environment.")
        return MockKiteConnect(api_key="MOCK_KEY")
