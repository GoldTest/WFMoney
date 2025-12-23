import os
import json
from datetime import datetime
from .config import get_data_path

class PositionManager:
    def __init__(self):
        self.file_path = str(get_data_path("positions.json"))
        self.positions = self._load_data()

    def _load_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading positions: {e}")
                return {}
        return {}

    def _save_data(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.positions, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving positions: {e}")

    def get_position(self, symbol):
        return self.positions.get(symbol, {
            "total_budget": 0,
            "total_units": 100,
            "history": []
        })

    def update_config(self, symbol, total_budget):
        if symbol not in self.positions:
            self.positions[symbol] = {"total_budget": 0, "total_units": 100, "history": []}
        self.positions[symbol]["total_budget"] = total_budget
        self._save_data()
        return self.positions[symbol]

    def add_record(self, symbol, date, units, price, conclusion=None):
        if symbol not in self.positions:
            self.positions[symbol] = {"total_budget": 0, "total_units": 100, "history": []}
        
        record = {
            "date": date,
            "units": units,
            "price": price,
            "amount": units * (self.positions[symbol]["total_budget"] / 100),
            "conclusion": conclusion
        }
        self.positions[symbol]["history"].append(record)
        # Sort history by date
        self.positions[symbol]["history"].sort(key=lambda x: x["date"])
        self._save_data()
        return self.positions[symbol]

    def delete_record(self, symbol, index):
        if symbol in self.positions and 0 <= index < len(self.positions[symbol]["history"]):
            self.positions[symbol]["history"].pop(index)
            self._save_data()
            return True
        return False

    def clear_positions(self, symbol):
        """Clear all records and reset budget for a symbol"""
        if symbol in self.positions:
            self.positions[symbol]["history"] = []
            self._save_data()
            return True
        return False

    def get_summary(self, symbol, current_price=None):
        pos = self.get_position(symbol)
        history = pos.get("history", [])
        total_budget = pos.get("total_budget", 0)
        unit_amount = total_budget / 100 if total_budget > 0 else 0
        
        processed_history = []
        running_units = 0
        total_cost_value = 0 # This tracks the total money spent on current holdings
        total_realized_pnl = 0
        
        # We need a way to track the average cost price (per share/unit of the asset, not per 'position unit')
        avg_cost_price = 0
        
        for r in history:
            units = r["units"] # Number of 'position units' (1-100)
            price = r["price"] # Price of the asset at that time
            
            pnl = 0
            if units > 0: # Buy
                # Calculate how much money this buy cost
                buy_amount = units * unit_amount
                
                # Update running average cost price of the asset
                if running_units + units > 0:
                    avg_cost_price = ((avg_cost_price * running_units) + (price * units)) / (running_units + units)
                
                running_units += units
                total_cost_value += buy_amount
                
            elif units < 0: # Sell
                sell_units = abs(units)
                if running_units > 0 and avg_cost_price > 0:
                    # P&L ratio = (price / avg_cost_price - 1)
                    # Total P&L = P&L ratio * sell_units * unit_amount
                    pnl = (price / avg_cost_price - 1) * sell_units * unit_amount
                    total_realized_pnl += pnl
                    
                    # Update running units and cost value
                    running_units -= sell_units
                    total_cost_value = running_units * unit_amount
                    
                    if running_units <= 0:
                        running_units = 0
                        avg_cost_price = 0
                        total_cost_value = 0
            
            # Note: if units == 0, it's a "no action" record, doesn't change anything
            
            processed_history.append({
                **r,
                "amount": abs(units) * unit_amount,
                "pnl": pnl
            })
            
        used_units = running_units
        remaining_units = pos["total_units"] - used_units
        
        # Unrealized P&L calculation fix
        unrealized_pnl = 0
        if current_price and used_units > 0 and avg_cost_price > 0:
            unrealized_pnl = (current_price / avg_cost_price - 1) * used_units * unit_amount
            
        total_pnl = total_realized_pnl + unrealized_pnl
        unrealized_pnl_pct = 0
        if current_price and avg_cost_price > 0:
            unrealized_pnl_pct = (current_price / avg_cost_price - 1)
            
        return {
            "symbol": symbol,
            "total_budget": total_budget,
            "used_units": used_units,
            "remaining_units": remaining_units,
            "avg_cost_price": avg_cost_price, # This is the price of the asset (e.g., 3919)
            "current_holdings_value": used_units * unit_amount, # This is the money value (e.g., 3000)
            "total_realized_pnl": total_realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "total_pnl": total_pnl,
            "history": processed_history
        }
