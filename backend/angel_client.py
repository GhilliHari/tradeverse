
import logging
import pyotp
from datetime import datetime
from SmartApi import SmartConnect
from config import config

logger = logging.getLogger("AngelClient")
print("--- ANGEL CLIENT VERSION: 2.1 (MANUAL_LTP_FIX) ---")

class AngelClient:
    def __init__(self, api_key, client_id, password, totp_key=None):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_key = totp_key
        self.smart_api = None
        self.token_map = {} # Cache for symbol -> token
        self._login()

    def _login(self):
        try:
            # Dynamic IP Detection
            default_ip = "106.193.147.98"
            try:
                import requests
                detected_ip = requests.get("https://api.ipify.org", timeout=5).text
                self.clientPublicIP = detected_ip
                logger.info(f"Dynamic IP Detection: {detected_ip}")
            except Exception as ipe:
                logger.warning(f"IP Detection failed, using fallback: {ipe}")
                self.clientPublicIP = default_ip

            self.smart_api = SmartConnect(api_key=self.api_key)
            self.smart_api.timeout = 15 # Explicitly set timeout to prevent infinite hangs if IP is blocked
            import socket
            socket.setdefaulttimeout(15) # Global fallback
            
            # Generate TOTP if key is provided
            totp_val = None
            if self.totp_key:
                try:
                    # Sanitize TOTP key: Remove spaces, dashes, and ensure it's uppercase
                    clean_totp = str(self.totp_key).replace(" ", "").replace("-", "").strip().upper()
                    
                    # Angel One TOTP secrets are base32. Check for invalid characters (0, 1, 8, 9)
                    invalid_chars = [c for c in clean_totp if c in "0189"]
                    if invalid_chars:
                        logger.error(f"TOTP key contains invalid base32 characters: {invalid_chars}")
                    
                    logger.info(f"Generating TOTP for {self.client_id}. Key Length: {len(clean_totp)}")
                    
                    import base64
                    try:
                        # Test if it's valid base32 (ignoring padding)
                        missing_padding = len(clean_totp) % 8
                        if missing_padding:
                            clean_totp_padded = clean_totp + '=' * (8 - missing_padding)
                        else:
                            clean_totp_padded = clean_totp
                        base64.b32decode(clean_totp_padded, casefold=True)
                        logger.info("Internal Base32 validation: SUCCESS")
                    except Exception as b32e:
                        logger.error(f"Internal Base32 validation FAILED: {b32e}")

                    totp = pyotp.TOTP(clean_totp)
                    totp_val = totp.now()
                    logger.info(f"Generated TOTP Code: {totp_val} at {datetime.now().strftime('%H:%M:%S')}")
                except Exception as e:
                    logger.error(f"Error generating TOTP for {self.client_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # Login
            data = self.smart_api.generateSession(self.client_id, self.password, totp_val)
            # Log login response length/status safely without modifying 'data'
            if data.get('status'):
                logger.info(f"Login Response: Status=True, JWT_LEN={len(data['data'].get('jwtToken', ''))}")
            else:
                logger.error(f"Login Response: Status=False, Message={data.get('message')}, ErrorCode={data.get('errorCode')}")
            
            if data['status'] == False:
                logger.error(f"Angel Login Failed: {data['message']}")
                raise Exception(f"Login Failed: {data['message']}")
            
            # Force tokens and strip "Bearer " if already present
            jwt = data['data']['jwtToken']
            if jwt.startswith("Bearer "):
                jwt = jwt.replace("Bearer ", "")
                logger.info("Stripped redundant 'Bearer ' prefix from login token")
                
            # Use SDK methods if available, otherwise set attributes
            if hasattr(self.smart_api, 'setAccessToken'):
                self.smart_api.setAccessToken(jwt)
            else:
                self.smart_api.access_token = jwt
                
            self.smart_api.jwtToken = jwt
            
            refresh_token = data['data']['refreshToken']
            if hasattr(self.smart_api, 'setRefreshToken'):
                self.smart_api.setRefreshToken(refresh_token)
            else:
                self.smart_api.refresh_token = refresh_token
            
            # Capture Session Info for manual fetches
            self.clientLocalIP = getattr(self.smart_api, 'clientLocalIP', '127.0.0.1')
            self.clientMacAddress = getattr(self.smart_api, 'clientMacAddress', '96:9a:ac:dd:ee:7b')
            
            logger.info(f"Login Metadata: JWT_LEN={len(jwt)}, DetectedPublicIP={self.clientPublicIP}")

            # Manually update session headers - this helps the SDK's internal requests
            if hasattr(self.smart_api, 'session'):
                self.smart_api.session.headers.update({
                    "Authorization": f"Bearer {jwt}",
                    "Content-type": "application/json",
                    "Accept": "application/json",
                    "X-PrivateKey": self.api_key,
                    "X-UserType": "USER",
                    "X-SourceID": "WEB",
                    "X-ClientLocalIP": self.clientLocalIP,
                    "X-ClientPublicIP": self.clientPublicIP,
                    "X-MACAddress": self.clientMacAddress
                })
                logger.info("Deep-injected headers into SDK session")
            
            self.feed_token = self.smart_api.getfeedToken()
            
            # SESSION & API KEY VERIFICATION: Test profile and orderbook to validate Trading API Key
            try:
                profile = self.smart_api.getProfile(jwt)
                if not profile or profile.get('status') == False or profile.get('success') == False:
                    err_msg = profile.get('message', 'Profile Check Failed') if profile else 'Profile Check Failed'
                    self.login_error = f"Angel API Key Error: {err_msg}"
                    raise Exception(self.login_error)
                
                # Test orderBook to verify Trading API Key validity
                ob_check = self.smart_api.orderBook()
                if isinstance(ob_check, dict) and (ob_check.get('status') == False or ob_check.get('success') == False):
                    err_msg = ob_check.get('message', 'Invalid API Key')
                    self.login_error = f"Angel API Key Invalid: {err_msg}"
                    logger.error(f"Trading API Key verification failed: {err_msg}")
                    raise Exception(self.login_error)

                logger.info(f"Verified Session for: {profile['data'].get('clientname', 'Unknown User')}")
            except Exception as e:
                logger.error(f"Session verification exception: {e}")
                self.login_error = str(e)
                raise

            logger.info("Angel Client fully initialized.")
            
        except Exception as e:
            logger.error(f"Angel Client Initialization Error: {e}")
            self.login_error = str(e)

    def get_login_error(self):
        return getattr(self, 'login_error', None)

    def is_connected(self):
        """
        Public method to check if the client is truly connected with a valid API Key.
        """
        if getattr(self, 'login_error', None):
            return False
            
        if not self.smart_api or not getattr(self.smart_api, 'jwtToken', None):
            return False
            
        # Check cache
        now = datetime.now()
        if hasattr(self, '_last_conn_check'):
            if (now - self._last_conn_check).total_seconds() < 60:
                return getattr(self, '_cached_conn_status', False)
        
        # Verify profile and JWT token validity
        try:
            self._last_conn_check = now
            p = self.smart_api.getProfile(self.smart_api.jwtToken)
            profile_ok = bool(p and (p.get('status') == True or p.get('success') == True) and p.get('data', {}).get('clientcode') is not None)
            self._cached_conn_status = profile_ok
            return profile_ok
        except Exception:
            if getattr(self.smart_api, 'jwtToken', None):
                return True
            self._cached_conn_status = False
            return False

    def profile(self):
        """
        Returns basic profile info for the UI.
        """
        logger.info(f"AngelClient.profile() called. self: {self}")
        if not self.smart_api:
            return {"user_id": "NOT_CONNECTED"}
        
        try:
            # Re-fetch or use cached info
            jwt = getattr(self.smart_api, 'jwtToken', None)
            if not jwt: return {"user_id": self.client_id, "user_name": "No Token"}
            
            p = self.smart_api.getProfile(jwt)
            logger.info(f"Full Profile API Response: {p}") # DEBUGGING MISSING INFO
            
            if p.get('status'):
                data = p.get('data', {})
                return {
                    "user_id": data.get('clientcode', self.client_id),
                    "user_name": data.get('clientname', 'Angel User'),
                    "email": data.get('email', 'N/A'),
                    "broker": "ANGEL",
                    "status": "LIVE"
                }
            return {"user_id": self.client_id, "user_name": "Session Error", "broker": "ANGEL", "status": "ERROR"}
        except Exception as e:
            logger.error(f"Error fetching Angel Profile: {e}")
            return {"user_id": self.client_id, "user_name": "Profile Error", "broker": "ANGEL", "status": "EXCEPTION"}
            
    def search_scrip(self, query, exchange="NSE"):
        """
        Searches for a scrip using the SmartAPI and returns matching results.
        """
        if not self.smart_api:
            return []
        
        try:
            logger.info(f"Searching for {query} on {exchange}")
            
            # Use the searchScrip API
            res = self.smart_api.searchScrip(exchange, query)
            
            if res and res.get('status') and res.get('data'):
                # Format results for the frontend
                results = []
                for scrip in res['data']:
                    results.append({
                        "symbol": scrip['tradingsymbol'],
                        "name": scrip.get('symboltoken', ''), # Using token as ID usually, or description if available
                        "token": scrip['symboltoken'],
                        "exchange": scrip['exchange']
                    })
                return results[:10] # Return top 10 matches
            return []
        except Exception as e:
            logger.error(f"Search API Failed: {e}")
            return []

    def _get_token_and_exchange(self, symbol_str):
        if symbol_str in self.token_map:
            return self.token_map[symbol_str]
            
        try:
            parts = symbol_str.split(":")
            exchange = parts[0] if len(parts) == 2 else "NSE"
            symbol = parts[1] if len(parts) == 2 else symbol_str
            
            # Standard Tokens for common indices in Angel One
            mapping = {
                "BANKNIFTY": ("NSE", "Nifty Bank", "99926009"),
                "NIFTY": ("NSE", "Nifty 50", "99926000"),
                "FINNIFTY": ("NSE", "Nifty Fin Services", "99926037"),
                "MIDCPNIFTY": ("NSE", "Nifty Midcap 100", "99926074"),
                "Nifty Bank": ("NSE", "Nifty Bank", "99926009"),
                "Nifty 50": ("NSE", "Nifty 50", "99926000"),
                "NIFTY MIDCAP 100": ("NSE", "Nifty Midcap 100", "99926074"),
                "SBIN": ("NSE", "SBIN-EQ", "3045"),
                "^NSEBANK": ("NSE", "Nifty Bank", "99926009"),
                "^NSEI": ("NSE", "Nifty 50", "99926000"),
                "^CNXFIN": ("NSE", "Nifty Fin Services", "99926037"),
                "^NSMIDCP": ("NSE", "Nifty Midcap 100", "99926074")
            }


            
            if symbol in mapping:
                res = mapping[symbol]
                self.token_map[symbol_str] = res
                return res
            
            logger.warning(f"Using generic lookup for {symbol}")
            return exchange, symbol, None
            
        except Exception as e:
            logger.error(f"Error parsing symbol {symbol_str}: {e}")
            return "NSE", symbol_str, None

    def ltp(self, instrument_token):
        if not self.smart_api: return {}
             
        # Initial resolution
        exchange, tradingsymbol, token = self._get_token_and_exchange(instrument_token)
            
        if not token: 
            logger.info(f"Resolving token for {instrument_token} via API search...")
            try:
                # Extract base symbol
                base_symbol = instrument_token.split(":")[-1]
                search_res = self.smart_api.searchScrip(exchange, base_symbol)
                if search_res.get('status') and search_res.get('data'):
                    # Pick the first matching symbol
                    match = search_res['data'][0]
                    tradingsymbol = match['tradingsymbol']
                    token = match['symboltoken']
                    logger.info(f"API Search Found: {tradingsymbol} -> {token}")
                    self.token_map[instrument_token] = (exchange, tradingsymbol, token)
            except Exception as e:
                logger.error(f"API Search Failed for {instrument_token}: {e}")
            
        if not token: 
            logger.warning(f"Could not resolve token for {instrument_token}")
            return {instrument_token: {"last_price": 0.0}}
              
        try:
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getLtpData"
            jwt = self.smart_api.jwtToken
            
            headers_base = {
                "Content-type": "application/json",
                "X-ClientLocalIP": getattr(self, 'clientLocalIP', '127.0.0.1'),
                "X-ClientPublicIP": getattr(self, 'clientPublicIP', '106.193.147.98'),
                "X-MACAddress": getattr(self, 'clientMacAddress', '96:9a:ac:dd:ee:7b'),
                "Accept": "application/json",
                "X-PrivateKey": self.api_key,
                "X-UserType": "USER",
                "X-SourceID": "WEB",
            }
            payload = {"exchange": exchange, "tradingsymbol": tradingsymbol, "symboltoken": token}
            
            import requests, json
            
            # ATTEMPT 1: SDK Request (Primary)
            try:
                res = self.smart_api.ltpData(exchange, tradingsymbol, token)
                if res.get('status'):
                    data_node = res['data']
                    ltp_val = data_node.get('ltp', data_node.get('last_price', 0))
                    return {instrument_token: {"instrument_token": token, "last_price": ltp_val}}
                elif res.get('errorCode') == 'AG8001':
                    logger.warning("Session Expired (AG8001) in SDK LTP. Refreshing...")
                    self._login() # Refresh session
                    # Retry once with new session
                    res = self.smart_api.ltpData(exchange, tradingsymbol, token)
                    if res.get('status'):
                        data_node = res['data']
                        ltp_val = data_node.get('ltp', data_node.get('last_price', 0))
                        return {instrument_token: {"instrument_token": token, "last_price": ltp_val}}

            except Exception as e:
                logger.warning(f"SDK LTP failed: {e}. Trying manual fallback...")

            # ATTEMPT 2: Manual Request (Bearer)
            h1 = headers_base.copy()
            h1["Authorization"] = f"Bearer {self.smart_api.jwtToken}"
            r1 = requests.post(url, headers=h1, data=json.dumps(payload))
            res = r1.json()
            
            if not res.get('status') and res.get('errorCode') == 'AG8001':
                logger.warning("Session Expired (AG8001) in Manual LTP. Refreshing...")
                self._login()
                h1["Authorization"] = f"Bearer {self.smart_api.jwtToken}"
                r1 = requests.post(url, headers=h1, data=json.dumps(payload))
                res = r1.json()

            if res.get('status'):
                data_node = res['data']
                ltp_val = data_node.get('ltp', data_node.get('last_price', 0))
                return {instrument_token: {"instrument_token": token, "last_price": ltp_val}}
            else:
                logger.error(f"LTP Final Failure for {instrument_token}: {res.get('message')} (Code: {res.get('errorCode')})")
                return {}
        except Exception as e:
             logger.error(f"Angel LTP Error: {e}")
             return {}

    def get_historical_data(self, exchange, token, interval, from_date, to_date):
        """
        Fetches historical candle data from Angel One.
        interval: "ONE_MINUTE", "FIVE_MINUTE", "TEN_MINUTE", "FIFTEEN_MINUTE", "THIRTY_MINUTE", "ONE_HOUR", "ONE_DAY"
        from_date: datetime object or "YYYY-MM-DD HH:MM" string
        to_date: datetime object or "YYYY-MM-DD HH:MM" string
        """
        if not self.smart_api:
            return []

        try:
            # Convert datetime to string if needed
            if isinstance(from_date, datetime):
                from_date_str = from_date.strftime("%Y-%m-%d %H:%M")
            else:
                from_date_str = from_date

            if isinstance(to_date, datetime):
                to_date_str = to_date.strftime("%Y-%m-%d %H:%M")
            else:
                to_date_str = to_date

            historicParam = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date_str,
                "todate": to_date_str
            }

            logger.info(f"Fetching historical data: {historicParam}")
            res = self.smart_api.getCandleData(historicParam)

            if res.get('status'):
                return res.get('data', [])
            else:
                logger.error(f"Historical Data Fetch Failed: {res.get('message')} (Code: {res.get('errorCode')})")
                return []
        except Exception as e:
            logger.error(f"Angel Historical Data Error: {e}")
            return []

    def _resolve_future(self, symbol):
        """
        Heuristic to find the front-month future for Nifty/BankNifty.
        """
        try:
            exchange = "NFO"
            # Search for symbol + "FUT"
            query = f"{symbol} FUT"
            logger.info(f"Searching for tradable future: {query}")
            res = self.smart_api.searchScrip(exchange, query)
            if res and res.get('status') and res.get('data'):
                # Heuristic: Pick the one that starts with the symbol and contains "FUT"
                # Usually the first one is the front month if sorted or most relevant.
                for scrip in res['data']:
                    tsym = scrip['tradingsymbol']
                    if tsym.startswith(symbol) and "FUT" in tsym:
                        logger.info(f"Resolved tradable future: {tsym} (Token: {scrip['symboltoken']})")
                        return exchange, tsym, scrip['symboltoken']
            return None, None, None
        except Exception as e:
            logger.error(f"Future resolution failed: {e}")
            return None, None, None

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, validity="DAY", tag=None):
        if not self.smart_api:
            raise Exception("Broker not connected")
            
        try:
            # Map parameters to Angel format
            angel_product = "INTRADAY" if product == "MIS" else "DELIVERY" 
            if product == "CNC": angel_product = "DELIVERY"
            if product == "NRML": angel_product = "CARRYFORWARD"
            
            # 1. TRADABLE RESOLUTION: If it's a non-tradable index, try to resolve to Future
            if tradingsymbol.upper() in ["BANKNIFTY", "NIFTY", "FINNIFTY"]:
                logger.info(f"Attempting to resolve {tradingsymbol} to a tradable instrument...")
                f_exchange, f_symbol, f_token = self._resolve_future(tradingsymbol.upper())
                if f_symbol:
                    exchange = f_exchange
                    tradingsymbol = f_symbol
                    res_exchange, res_symbol, res_token = f_exchange, f_symbol, f_token
                else:
                    # Fallback to standard mapping (likely will fail on order placement)
                    res_exchange, res_symbol, res_token = self._get_token_and_exchange(f"{exchange}:{tradingsymbol}")
            else:
                # RESOLVE SYMBOL AND TOKEN (Standard Fix)
                res_exchange, res_symbol, res_token = self._get_token_and_exchange(f"{exchange}:{tradingsymbol}")
            
            orderparams = {
                "variety": "NORMAL", 
                "tradingsymbol": res_symbol, # Use resolved symbol (e.g. SBIN-EQ)
                "symboltoken": res_token,
                "transactiontype": transaction_type,
                "exchange": res_exchange,
                "ordertype": order_type,
                "producttype": angel_product,
                "duration": validity,
                "price": price if price else 0,
                "quantity": quantity
            }
            
            if not orderparams["symboltoken"]:
                 raise Exception(f"Could not resolve token for {tradingsymbol}")
            
            # Log the final parameters being sent
            logger.info(f"Placing Angel Order: {res_symbol} ({res_token}) Qty:{quantity} {transaction_type}")

            order_id = self.smart_api.placeOrder(orderparams)
            
            # Handle Session Expire
            if isinstance(order_id, dict) and order_id.get('errorCode') == 'AG8001':
                 logger.warning("Session Expired (AG8001) in place_order. Retrying...")
                 self._login()
                 order_id = self.smart_api.placeOrder(orderparams)

            logger.info(f"Order placed via Angel. ID: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Angel Order Placement Error: {e}")
            raise

    def modify_order(self, order_id, price=None, quantity=None, order_type="LIMIT", variety="NORMAL", product="MIS", tradingsymbol=None, exchange="NFO", symboltoken=None):
        if not self.smart_api:
            raise Exception("Broker not connected")
        try:
            angel_product = "INTRADAY" if product == "MIS" else "DELIVERY"
            if product == "NRML": angel_product = "CARRYFORWARD"
            res_token = symboltoken
            res_symbol = tradingsymbol
            if not res_token and tradingsymbol:
                _, res_symbol, res_token = self._get_token_and_exchange(f"{exchange}:{tradingsymbol}")
            orderparams = {
                "variety": variety or "NORMAL",
                "orderid": str(order_id),
                "ordertype": order_type,
                "producttype": angel_product,
                "duration": "DAY",
                "price": price if price else 0,
                "quantity": quantity if quantity else 1,
                "tradingsymbol": res_symbol,
                "symboltoken": res_token or "",
                "exchange": exchange
            }
            logger.info(f"Modifying Angel Order {order_id}: Price={price}, Qty={quantity}")
            return self.smart_api.modifyOrder(orderparams)
        except Exception as e:
            logger.error(f"Angel Order Modification Error: {e}")
            raise

    def cancel_order(self, order_id, variety="NORMAL"):
        if not self.smart_api:
            raise Exception("Broker not connected")
        try:
            logger.info(f"Cancelling Angel Order: {order_id}")
            return self.smart_api.cancelOrder(str(order_id), variety or "NORMAL")
        except Exception as e:
            logger.error(f"Angel Cancel Order Error: {e}")
            raise

    def get_option_chain(self, symbol="NSE:BANKNIFTY", expiry=None):
        """
        Fetches the option chain with real-time OI and LTP using marketData API.
        """
        if not self.smart_api:
            return []

        try:
            # 1. Get Spot Price
            ltp_data = self.ltp(symbol)
            if symbol not in ltp_data:
                return []
            
            last_price = ltp_data[symbol]['last_price']
            
            # 2. Dynamic Strike Step selection
            strike_step = 100
            search_query = "BANKNIFTY"
            
            if "FIN" in symbol.upper():
                strike_step = 50 # Fin Nifty usually 50/100
                search_query = "FINNIFTY"
            elif "MID" in symbol.upper():
                strike_step = 25 # Midcap Nifty is 25/50
                search_query = "MIDCPNIFTY"
            elif "NIFTY" in symbol.upper() and "BANK" not in symbol.upper():
                strike_step = 50 
                search_query = "NIFTY"
            
            base_strike = round(last_price / strike_step) * strike_step
            
            logger.info(f"Fetching real-time option chain for {search_query} around {base_strike} (Step: {strike_step})")

            
            # Gather all tokens
            strike_data = {}
            nfo_tokens = []
            
            for i in range(-5, 6):
                strike = base_strike + (i * strike_step)

                ce_sym = f"{search_query}{strike}CE"
                pe_sym = f"{search_query}{strike}PE"
                
                _, _, ce_token = self._get_token_and_exchange(f"NFO:{ce_sym}")
                _, _, pe_token = self._get_token_and_exchange(f"NFO:{pe_sym}")
                
                strike_data[strike] = {
                    "strike": strike,
                    "ce_token": ce_token,
                    "pe_token": pe_token,
                    "ce_premium": 0,
                    "pe_premium": 0,
                    "oi_ce": 0,
                    "oi_pe": 0
                }
                
                if ce_token: nfo_tokens.append(ce_token)
                if pe_token: nfo_tokens.append(pe_token)
                
            # Fetch Market Data in Bulk
            if nfo_tokens:
                try:
                    mode = "FULL"
                    exchangeTokens = {"NFO": nfo_tokens}
                    res = self.smart_api.getMarketData(mode, exchangeTokens)
                    
                    if res and res.get('status') and res.get('data'):
                        market_data_list = res.get('data', {}).get('fetched', [])
                        if not market_data_list and isinstance(res.get('data'), list):
                             market_data_list = res['data']
                             
                        # Map fetched data to strikes
                        token_to_data = {str(item.get('symbolToken', item.get('symboltoken', ''))): item for item in market_data_list}
                        
                        for strike_val, sd in strike_data.items():
                            if sd['ce_token'] and str(sd['ce_token']) in token_to_data:
                                item = token_to_data[str(sd['ce_token'])]
                                # Some API versions return opnInterest, others oi
                                sd['ce_premium'] = item.get('ltp', item.get('last_price', 0))
                                sd['oi_ce'] = item.get('opnInterest', item.get('oi', 0))
                                
                            if sd['pe_token'] and str(sd['pe_token']) in token_to_data:
                                item = token_to_data[str(sd['pe_token'])]
                                sd['pe_premium'] = item.get('ltp', item.get('last_price', 0))
                                sd['oi_pe'] = item.get('opnInterest', item.get('oi', 0))
                except Exception as md_err:
                     logger.warning(f"Bulk marketData failed: {md_err}. Falling back to default mock premiums.")
                     
            # Formatting Final Return
            strikes = []
            for strike_val in sorted(strike_data.keys()):
                sd = strike_data[strike_val]
                
                # Mock if 0 (token search failure or API error)
                if sd['ce_premium'] == 0: sd['ce_premium'] = max(10, (last_price - strike_val) + 100)
                if sd['pe_premium'] == 0: sd['pe_premium'] = max(10, (strike_val - last_price) + 100)
                
                strikes.append({
                    "strike": strike_val,
                    "ce_premium": float(sd['ce_premium']),
                    "pe_premium": float(sd['pe_premium']),
                    "oi_ce": int(sd['oi_ce']),
                    "oi_pe": int(sd['oi_pe'])
                })

            return strikes
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def orders(self):
        """
        Fetches the order book from Angel One.
        """
        if not self.smart_api:
            return []
            
        try:
            res = self.smart_api.orderBook()
            if res.get('status'):
                data = res.get('data', [])
                if data is None: return [] # API returns None for empty book sometimes
                
                # Normalize keys to match Kite format roughly for UI compatibility
                normalized_orders = []
                for o in data:
                    normalized_orders.append({
                        "order_id": o.get("orderid"),
                        "exchange_order_id": o.get("uniqueorderid"),
                        "status": o.get("status"), # e.g. "complete", "rejected"
                        "tradingsymbol": o.get("tradingsymbol"),
                        "exchange": o.get("exchange"),
                        "transaction_type": o.get("transactiontype"),
                        "quantity": o.get("quantity"),
                        "filled_quantity": o.get("filledshares"),
                        "price": o.get("price"),
                        "average_price": o.get("averageprice"),
                        "product": o.get("producttype"),
                        "order_timestamp": o.get("updatetime")
                    })
                return normalized_orders
            else:
                logger.error(f"Order fetch failed: {res.get('message')}")
                return []
        except Exception as e:
            logger.error(f"Angel Order Fetch Error: {e}")
            return []

    def liquidate_all_positions(self):
        """
        EMERGENCY KILL SWITCH: Liquidates ALL open positions and cancels open orders.
        """
        logger.critical("🚨 EMERGENCY PROTOCOL INITIATED: LIQUIDATING ALL POSITIONS 🚨")
        
        try:
            # 1. Cancel All Pending Orders
            orders = self.smart_api.orderBook()
            if orders and isinstance(orders, dict) and orders.get('status'):
                orders_data = orders.get('data') or []
                for order in orders_data:
                    if order.get('orderstatus') in ['open', 'trigger pending']:
                        try:
                            self.smart_api.cancelOrder(order['orderid'], "NORMAL")
                            logger.info(f"Cancelled Order {order['orderid']}")
                        except: pass

            # 2. Square Off All Positions
            positions = self.smart_api.position()
            if positions and isinstance(positions, dict) and positions.get('status'):
                data = positions.get('data') or []
                if not data:
                    logger.info("No open positions to liquidate.")
                    
                for pos in data:
                    net_qty = int(pos.get('netqty', 0))
                    if net_qty != 0:
                        symbol = pos['tradingsymbol']
                        token = pos['symboltoken']
                        
                        # Determine Exit Action
                        transaction_type = "SELL" if net_qty > 0 else "BUY"
                        qty = abs(net_qty)
                        
                        logger.warning(f"Liquidating: {symbol} (Qty: {qty}) -> {transaction_type}")
                        
                        order_params = {
                            "variety": "NORMAL",
                            "tradingsymbol": symbol,
                            "symboltoken": token,
                            "transactiontype": transaction_type,
                            "exchange": pos.get('exchange', 'NFO'),
                            "ordertype": "MARKET",
                            "producttype": pos.get('producttype', 'INTRADAY'),
                            "duration": "DAY",
                            "quantity": str(qty)
                        }
                        
                        try:
                            self.smart_api.placeOrder(order_params)
                            logger.info(f"✔ Liquidation Order Placed for {symbol}")
                        except Exception as e:
                            logger.error(f"❌ Failed to Liquidate {symbol}: {e}")
            return True

        except Exception as e:
            logger.error(f"CRITICAL FAILURE IN LIQUIDATION: {e}")
            return False
