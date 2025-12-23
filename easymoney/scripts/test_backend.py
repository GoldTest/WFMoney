import requests
import json

def test_backend():
    base_url = "http://localhost:8000"
    
    print("\nTesting Indices endpoint...")
    try:
        resp = requests.get(f"{base_url}/api/market/indices")
        data = resp.json()
        print(f"Received {len(data)} indices")
        for name, info in data.items():
            print(f"- {name}: {info['price']} ({info['pct_change']:.2f}%)")
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting AI Analysis for AAPL...")
    try:
        resp = requests.get(f"{base_url}/api/market/analyze?symbol=AAPL")
        data = resp.json()
        if "analysis" in data:
            print("AI Analysis success!")
            print("Analysis preview:", data["analysis"][:200])
        else:
            print("AI Analysis error:", data)
    except Exception as e:
        print(f"Error: {e}")

    print("\nTesting History for AAPL...")
    try:
        resp = requests.get(f"{base_url}/api/market/history?symbol=AAPL&period=1mo")
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"Received {len(data)} history records for AAPL")
            print("First record:", data[0])
        else:
            print("No history data or error:", data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_backend()
