
import pytest
from unittest.mock import MagicMock, patch
from angel_client import AngelClient

class TestOrderMapping:
    @patch('angel_client.SmartConnect')
    def test_sbin_mapping(self, MockSmartConnect):
        # Mock SmartConnect instance
        mock_api = MockSmartConnect.return_value
        mock_api.generateSession.return_value = {
            'status': True,
            'data': {'jwtToken': 'mock_jwt', 'refreshToken': 'mock_refresh'}
        }
        mock_api.getProfile.return_value = {'status': True, 'data': {}}
        mock_api.placeOrder.return_value = "ORDER123"

        # Initialize client (it will login once)
        client = AngelClient("api_key", "client_id", "password", "totp")
        
        # Test place_order for SBIN
        # It should resolve SBIN to SBIN-EQ and token 3045
        client.place_order(
            variety="NORMAL",
            exchange="NSE",
            tradingsymbol="SBIN",
            transaction_type="BUY",
            quantity=1,
            product="MIS",
            order_type="LIMIT",
            price=100
        )
        
        # Check if smart_api.placeOrder was called with EXPECTED tradingsymbol
        args, kwargs = mock_api.placeOrder.call_args
        order_params = args[0]
        
        assert order_params['tradingsymbol'] == "SBIN-EQ"
        assert order_params['symboltoken'] == "3045"
        assert order_params['exchange'] == "NSE"
        print("\nSUCCESS: SBIN correctly mapped to SBIN-EQ/3045")

    @patch('angel_client.SmartConnect')
    def test_banknifty_mapping(self, MockSmartConnect):
        mock_api = MockSmartConnect.return_value
        mock_api.generateSession.return_value = {
            'status': True,
            'data': {'jwtToken': 'mock_jwt', 'refreshToken': 'mock_refresh'}
        }
        mock_api.getProfile.return_value = {'status': True, 'data': {}}
        mock_api.placeOrder.return_value = "ORDER123"

        client = AngelClient("api_key", "client_id", "password", "totp")
        
        # Test place_order for BANKNIFTY
        client.place_order(
            variety="NORMAL",
            exchange="NSE",
            tradingsymbol="BANKNIFTY",
            transaction_type="BUY",
            quantity=15,
            product="MIS",
            order_type="MARKET"
        )
        
        args, _ = mock_api.placeOrder.call_args
        order_params = args[0]
        
        assert order_params['tradingsymbol'] == "Nifty Bank"
        assert order_params['symboltoken'] == "99926009"
        print("SUCCESS: BANKNIFTY correctly mapped to Nifty Bank/99926009")

if __name__ == "__main__":
    # If run directly, run the tests without manual patch pass
    print("Running Symbol Mapping Tests...")
    t = TestOrderMapping()
    t.test_sbin_mapping()
    t.test_banknifty_mapping()
