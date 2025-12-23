from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .utils import MarketDataFetcher
from .ai_analyzer import AIAnalyzer
from .position_manager import PositionManager
import pandas as pd
import json

class ConfigUpdate(BaseModel):
    api_key: str = None
    base_url: str = None
    model_name: str = None

class PositionConfig(BaseModel):
    symbol: str
    total_budget: float

class PositionRecord(BaseModel):
    symbol: str
    date: str
    units: float
    price: float

app = FastAPI(title="WFMoney API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = AIAnalyzer()
pos_manager = PositionManager()

@app.get("/api/config")
def get_config():
    """Get current AI configuration (obfuscated)"""
    return {
        "api_key": f"{analyzer.api_key[:4]}...{analyzer.api_key[-4:]}" if analyzer.api_key and len(analyzer.api_key) > 8 else "Not Set",
        "base_url": analyzer.base_url or "Default (OpenAI)",
        "model_name": analyzer.model_name,
        "is_demo": analyzer.client is None
    }

@app.post("/api/config")
def update_config(config: ConfigUpdate):
    """Update AI configuration"""
    analyzer.update_config(api_key=config.api_key, base_url=config.base_url, model_name=config.model_name)
    return {"status": "success", "is_demo": analyzer.client is None}

@app.get("/api/market/quote")
def get_quote(symbol: str):
    """Get latest quote for a symbol"""
    df = MarketDataFetcher.get_data(symbol, period="1d", interval="1m")
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        return {
            "symbol": symbol,
            "price": float(latest['Close']),
            "change": float(latest['Close'] - df.iloc[0]['Close']),
            "pct_change": float((latest['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close'] * 100),
            "time": str(latest['Date'])
        }
    return {"error": "Symbol not found or data unavailable"}

@app.get("/api/market/history")
def get_history(symbol: str, period: str = "1y", interval: str = "1d"):
    """Get historical data with indicators"""
    df = MarketDataFetcher.get_data(symbol, period=period, interval=interval)
    if df is not None:
        df = MarketDataFetcher.calculate_indicators(df)
        # Convert to list of dicts for JSON
        data = df.to_dict(orient="records")
        # Handle datetime conversion
        for item in data:
            item['Date'] = str(item['Date'])
        return data
    return {"error": "Failed to fetch history"}

@app.get("/api/market/analyze")
def analyze_market(symbol: str, sim_date: str = Query(None)):
    """Get AI analysis for a symbol with position context (streaming)"""
    df = MarketDataFetcher.get_data(symbol, period="1y", interval="1d")
    if df is not None:
        df = MarketDataFetcher.calculate_indicators(df)
        pos_summary = pos_manager.get_summary(symbol)
        
        def generate():
            for chunk in analyzer.analyze_market_stream(symbol, df, pos_summary, pos_manager=pos_manager, sim_date=sim_date):
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")
    return {"error": "Data unavailable for analysis"}

@app.get("/api/positions/summary")
def get_position_summary(symbol: str):
    """Get position summary for a symbol with P&L stats"""
    # Try to get current price for unrealized P&L calculation
    current_price = None
    df = MarketDataFetcher.get_data(symbol, period="1d", interval="1m")
    if df is not None and not df.empty:
        current_price = float(df.iloc[-1]['Close'])
        
    return pos_manager.get_summary(symbol, current_price=current_price)

@app.post("/api/positions/config")
def update_position_config(config: PositionConfig):
    """Update total budget for a symbol"""
    return pos_manager.update_config(config.symbol, config.total_budget)

@app.post("/api/positions/record")
def add_position_record(record: PositionRecord):
    """Add a buy record"""
    return pos_manager.add_record(record.symbol, record.date, record.units, record.price)

@app.delete("/api/positions/record")
def delete_position_record(symbol: str, index: int):
    """Delete a buy record"""
    if pos_manager.delete_record(symbol, index):
        return {"status": "success"}
    return {"error": "Failed to delete record"}

@app.delete("/api/positions/clear")
def clear_positions(symbol: str):
    """Clear all records for a symbol"""
    if pos_manager.clear_positions(symbol):
        return {"status": "success"}
    return {"error": "Failed to clear positions"}

@app.get("/api/market/indices")
def get_major_indices():
    """Get quotes for major global indices and crypto"""
    indices_config = {
        "标普 500": "^GSPC",
        "纳斯达克 100": "^IXIC",
        "上证指数": "000001.SS",
        "恒生指数": "^HSI",
        "沪深 300": "000300.SS",
        "日经 225": "^N225",
        "比特币": "BTC-USD",
        "以太坊": "ETH-USD"
    }
    
    results = {}
    for name, symbol in indices_config.items():
        try:
            # Add Nikkei 225 to fallbacks in utils if needed, but yfinance usually works for it
            df = MarketDataFetcher.get_data(symbol, period="10d", interval="1d")
            
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                results[name] = {
                    "symbol": symbol,
                    "price": float(latest['Close']),
                    "change": float(latest['Close'] - prev['Close']),
                    "pct_change": float((latest['Close'] - prev['Close']) / prev['Close'] * 100)
                }
        except Exception as e:
            print(f"Error processing index {name}: {e}")
            continue
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
