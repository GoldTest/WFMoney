import yfinance as yf
import akshare as ak
import pandas as pd
import diskcache as dc
import os
import requests
from datetime import datetime, timedelta

# Initialize cache in the data directory
cache = dc.Cache("data/market_cache")

# Setup cache
cache = dc.Cache("data/market_cache")

class MarketDataFetcher:
    @staticmethod
    def get_data(symbol: str, period: str = "1y", interval: str = "1d"):
        """Generic data fetcher with caching and multiple sources"""
        cache_key = f"{symbol}_{period}_{interval}"
        if cache_key in cache:
            return cache[cache_key]

        df = None
        # Try yfinance first
        try:
            print(f"Fetching {symbol} with yfinance...")
            # yfinance 0.2.40+ requires curl_cffi for some endpoints, 
            # but let's try without session first as it's more reliable now
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df is not None and not df.empty:
                print(f"yfinance success for {symbol}")
                df = df.reset_index()
                cache.set(cache_key, df, expire=300)
                return df
        except Exception as e:
            print(f"yfinance failed for {symbol}: {e}")

        # Fallback to akshare for specific markets
        try:
            if symbol.startswith("^") or symbol.endswith(".SS") or symbol.endswith(".SZ"):
                print(f"Using akshare fallback for Index/A-share {symbol}")
                if symbol == "^GSPC":
                    df = ak.index_global_hist_em(symbol="标普500")
                elif symbol == "^IXIC":
                    df = ak.index_global_hist_em(symbol="纳斯达克")
                elif symbol == "^HSI":
                    df = ak.index_global_hist_em(symbol="恒生指数")
                elif symbol == "^N225":
                    df = ak.index_global_hist_em(symbol="日经225")
                elif symbol == "000001.SS":
                    df = ak.stock_zh_index_daily(symbol="sh000001")
                elif symbol == "000300.SS":
                    df = ak.stock_zh_index_daily(symbol="sh000300")
                elif symbol.endswith(".SS") or symbol.endswith(".SZ"):
                    df = MarketDataFetcher.get_ashare_data("sh" + symbol.split(".")[0] if symbol.endswith(".SS") else "sz" + symbol.split(".")[0])
                
                if df is not None and not df.empty:
                    # Robust column mapping
                    cols_map = {
                        '日期': 'Date', 'date': 'Date',
                        '开盘': 'Open', 'open': 'Open',
                        '最高': 'High', 'high': 'High',
                        '最低': 'Low', 'low': 'Low',
                        '收盘': 'Close', 'close': 'Close', '最新价': 'Close',
                        '成交量': 'Volume', 'volume': 'Volume'
                    }
                    new_cols = {}
                    for c in df.columns:
                        if c in cols_map:
                            new_cols[c] = cols_map[c]
                    
                    df = df.rename(columns=new_cols)
                    # Ensure basic columns exist
                    for col in ['Open', 'High', 'Low', 'Close']:
                        if col not in df.columns and 'Close' in df.columns:
                            df[col] = df['Close'] # Fallback
                    
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
            elif "-" in symbol and "USD" in symbol: # Crypto like BTC-USD
                crypto_symbol = symbol.replace("-USD", "").upper() + "USDT"
                print(f"Using Binance fallback for Crypto {crypto_symbol}")
                try:
                    url = f"https://api.binance.com/api/v3/klines?symbol={crypto_symbol}&interval=1d&limit=1000"
                    resp = requests.get(url, timeout=10)
                    data = resp.json()
                    if data and isinstance(data, list):
                        df = pd.DataFrame(data, columns=[
                            'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
                            'CloseTime', 'QuoteAssetVolume', 'NumberTrades',
                            'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume', 'Ignore'
                        ])
                        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
                        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                            df[col] = pd.to_numeric(df[col])
                        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                except Exception as e:
                    print(f"Binance fallback failed: {e}")
            elif symbol.isalpha() and len(symbol) <= 5: # Likely US Stock like AAPL
                print(f"Using akshare fallback for US Stock {symbol}")
                try:
                    df = ak.stock_us_hist(symbol=symbol, period="daily", adjust="")
                    if df is not None and not df.empty:
                        df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
                        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                        df['Date'] = pd.to_datetime(df['Date'])
                except:
                    df = ak.stock_us_daily(symbol=symbol, adjust="")
                    if df is not None and not df.empty:
                        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                        df['Date'] = pd.to_datetime(df['Date'])
            
            if df is not None and not df.empty:
                cache.set(cache_key, df, expire=300)
                return df
        except Exception as e:
            print(f"akshare fallback failed for {symbol}: {e}")

        return None

    @staticmethod
    def get_ashare_data(symbol: str, period: str = "daily"):
        """Specialized A-share fetcher using akshare"""
        cache_key = f"ak_{symbol}_{period}"
        if cache_key in cache:
            return cache[cache_key]
        
        try:
            # akshare symbol format: 'sh600000'
            df = ak.stock_zh_a_hist(symbol=symbol[2:], period=period, adjust="qfq")
            if df is not None and not df.empty:
                cols_map = {
                    '日期': 'Date', '开盘': 'Open', '最高': 'High', 
                    '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'
                }
                present_cols = [c for c in cols_map.keys() if c in df.columns]
                df = df[present_cols].rename(columns={c: cols_map[c] for c in present_cols})
                df['Date'] = pd.to_datetime(df['Date'])
                cache.set(cache_key, df, expire=300)
                return df
        except Exception as e:
            print(f"Error fetching A-share {symbol}: {e}")
        return None

    @staticmethod
    def calculate_indicators(df: pd.DataFrame):
        """Calculate basic technical indicators"""
        if df is None or df.empty or len(df) < 2:
            return df
        
        try:
            # Simple Moving Averages
            df['MA5'] = df['Close'].rolling(window=min(5, len(df))).mean()
            df['MA20'] = df['Close'].rolling(window=min(20, len(df))).mean()
            df['MA60'] = df['Close'].rolling(window=min(60, len(df))).mean()
            
            # RSI (Relative Strength Index) - Wilder's Smoothing
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0))
            loss = (-delta.where(delta < 0, 0))
            
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Simple RS calculation
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['Signal']
            
            # Bollinger Bands
            df['BB_Mid'] = df['Close'].rolling(window=20).mean()
            df['BB_Std'] = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
            df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
            
            # Replace NaN with 0 or drop them for JSON compliance
            df = df.fillna(0)
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            
        return df
