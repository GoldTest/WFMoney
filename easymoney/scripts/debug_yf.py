import yfinance as yf
import pandas as pd

def test_yf():
    symbols = ["AAPL", "BTC-USD", "^GSPC"]
    for symbol in symbols:
        print(f"Testing {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d")
            if df is not None and not df.empty:
                print(f"Success! Got {len(df)} rows for {symbol}")
                print(df.tail(1))
            else:
                print(f"Failed to get data for {symbol}")
        except Exception as e:
            print(f"Error for {symbol}: {e}")

if __name__ == "__main__":
    test_yf()
