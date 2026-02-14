import requests
import json

def test_brain_api():
    base_url = "http://localhost:8000"
    symbol = "NSE:BANKNIFTY"
    
    print(f"Testing Brain Intelligence API for {symbol}...")
    try:
        response = requests.get(f"{base_url}/api/intelligence/brain?symbol={symbol}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
            
            # Verify structure
            assert "model_scores" in data, "model_scores missing from response"
            scores = data["model_scores"]
            required_keys = ["technical", "tft", "rl", "sentiment", "options"]
            for key in required_keys:
                assert key in scores, f"Key '{key}' missing from model_scores"
                print(f"✅ {key.capitalize()}: {scores[key]}")
            
            print("\nFinal Test Result: PASS")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_brain_api()
