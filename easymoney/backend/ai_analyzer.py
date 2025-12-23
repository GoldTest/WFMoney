import os
import json
from datetime import datetime
from openai import OpenAI
import pandas as pd

class AIAnalyzer:
    def __init__(self, api_key=None, base_url=None, model_name=None):
        self.config_path = os.path.join(os.path.dirname(__file__), "ai_config.json")
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        
        # Load from file if exists, otherwise use env or defaults
        self._load_config()
        
        # Override with env if still not set
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.base_url:
            self.base_url = os.getenv("OPENAI_BASE_URL")
        if not self.model_name:
            self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            
        self.update_config(self.api_key, self.base_url, self.model_name, save=False)

    def _load_config(self):
        """Load configuration from local JSON file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key", self.api_key)
                    self.base_url = config.get("base_url", self.base_url)
                    self.model_name = config.get("model_name", self.model_name)
            except Exception as e:
                print(f"Error loading AI config: {e}")

    def _save_config(self):
        """Save current configuration to local JSON file"""
        try:
            config = {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "model_name": self.model_name
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving AI config: {e}")

    def update_config(self, api_key: str = None, base_url: str = None, model_name: str = None, save: bool = True):
        """Update AI configuration and re-initialize client"""
        if api_key is not None:
            self.api_key = api_key
        if base_url is not None:
            self.base_url = base_url
        if model_name is not None:
            self.model_name = model_name
            
        # Only initialize client if api_key is valid and not placeholder
        if self.api_key and self.api_key not in ["YOUR_API_KEY", ""]:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            
        if save:
            self._save_config()

    def _generate_mock_report(self, symbol: str, df: pd.DataFrame) -> str:
        """Generate a professional mock report when AI is disabled"""
        if df is None or df.empty or len(df) < 2:
            return f"### 🤖 AI 市场分析报告: {symbol}\n\n数据不足，无法生成分析报告。"

        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = (last_price - prev_price) / prev_price * 100
        
        rsi = df['RSI'].iloc[-1]
        ma5 = df['MA5'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        
        trend = "看涨 (Bullish)" if ma5 > ma20 else "看跌 (Bearish)"
        rsi_signal = "超买 (Overbought)" if rsi > 70 else ("超卖 (Oversold)" if rsi < 30 else "中性 (Neutral)")

        return f"""### 🤖 AI 市场分析报告: {symbol} (演示模式)

**1. 价格走势分析**
- 当前价格: {last_price:.2f}
- 日内涨跌: {change:+.2f}%
- 趋势判断: {trend} (基于MA5/MA20)

**2. 技术指标解读**
- **RSI (14)**: {rsi:.2f} - 当前处于 {rsi_signal} 区域。
- **均线系统**: 价格当前位于 MA5 ({ma5:.2f}) {'上方' if last_price > ma5 else '下方'}，短期走势{'偏强' if last_price > ma5 else '偏弱'}。
- **MACD**: 柱状图显示动能正在{'增强' if df['MACD_Hist'].iloc[-1] > df['MACD_Hist'].iloc[-2] else '减弱'}。

**3. 操作建议 (仅供参考)**
- 支撑位: {df['Low'].tail(5).min():.2f}
- 阻力位: {df['High'].tail(5).max():.2f}
- 策略建议: 市场当前处于 {trend} 阶段，建议关注 {rsi_signal} 信号的修复机会。

---
*注：此报告由系统基于技术指标自动生成。如需更深度 AI 洞察，请在 `backend/ai_analyzer.py` 中配置您的 API Key。*"""

    def analyze_market_stream(self, symbol: str, df: pd.DataFrame, pos_summary: dict = None, pos_manager=None, sim_date: str = None):
        """Analyze market data using LLM with streaming support and tools"""
        try:
            # 1. 如果是预演模式，截断数据到 sim_date
            if sim_date:
                yield f"> 🧪 **预演模式**: 当前模拟日期为 `{sim_date}`\n\n"
                # 找到 sim_date 在 df 中的位置
                df['DateStr'] = df['Date'].dt.strftime('%Y-%m-%d')
                mask = df['DateStr'] <= sim_date
                df = df[mask].copy()
                if df.empty:
                    yield f"❌ 预演日期 {sim_date} 不在历史数据范围内。\n"
                    return
                latest_price = float(df.iloc[-1]['Close'])
                sim_date = df.iloc[-1]['DateStr'] # 确保日期格式统一
                
                # 在预演模式下，需要根据模拟当天的价格重新计算仓位摘要
                if pos_manager:
                    pos_summary = pos_manager.get_summary(symbol, current_price=latest_price)
            else:
                latest_price = float(df.iloc[-1]['Close'])
            
            yield "> 🔍 **系统状态**: 正在获取实时行情与历史仓位数据...\n\n"
            
            if df is None or df.empty:
                yield "No data available for analysis."
                return

            if not self.client:
                yield self._generate_mock_report(symbol, df)
                return
            
            # Prepare data
            latest = df.iloc[-1]
            
            # Prepare historical data (last 5 cycles)
            hist_5 = df.tail(5).copy()
            hist_5['Date'] = hist_5['Date'].astype(str)
            hist_context = hist_5[['Date', 'Close', 'RSI', 'MACD', 'MA5', 'MA20']].to_dict(orient="records")
            
            # Ensure pos_summary has all required keys to avoid KeyErrors
            if not pos_summary:
                pos_summary = {
                    'used_units': 0, 
                    'avg_cost_price': 0, 
                    'unrealized_pnl_pct': 0,
                    'history': []
                }
            else:
                # Fill in missing keys if any
                pos_summary.setdefault('used_units', 0)
                pos_summary.setdefault('avg_cost_price', 0)
                pos_summary.setdefault('unrealized_pnl_pct', 0)
                pos_summary.setdefault('history', [])

            pos_context = f"当前持仓状态: {pos_summary['used_units']}/100 份\n"
            pos_context += f"当前持仓均价: {pos_summary['avg_cost_price']:.2f}\n"
            pos_context += f"当前持仓收益率: {pos_summary.get('unrealized_pnl_pct', 0)*100:.2f}%\n"
            pos_context += "近期交易记录:\n"
            for r in pos_summary['history'][-10:]:
                action = "买入" if r['units'] > 0 else ("卖出" if r['units'] < 0 else "不操作")
                conclusion_str = f" | 结论: {r.get('conclusion', r.get('reason', '无'))}"
                pos_context += f"- {r['date']}: {action} {abs(r['units'])} 份 @ {r['price']:.2f}{conclusion_str}\n"

            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "execute_trade",
                        "description": "执行买入或卖出操作。注意：只能操作当天，价格将自动按当前收盘价计算。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "enum": ["buy", "sell"],
                                    "description": "操作类型：buy (买入) 或 sell (卖出)"
                                },
                                "units": {
                                    "type": "number",
                                    "description": "操作份数 (1-100)"
                                },
                                "conclusion": {
                                    "type": "string",
                                    "description": "做出此交易决策的简要理由（将记录在交易历史中）"
                                }
                            },
                            "required": ["action", "units", "conclusion"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "no_action",
                        "description": "决定当日不执行任何买入或卖出操作。调用此工具将记录一条当日的‘不操作’历史，以确认分析已完成。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reason": {
                                    "type": "string",
                                    "description": "不操作的简要原因（将记录在交易历史中）"
                                }
                            },
                            "required": ["reason"]
                        }
                    }
                }
            ]

            system_prompt = f"""你是一个专业的股票/加密货币分析师和交易员。
请基于提供的历史K线数据和当前的持仓情况，给出今日的分析报告和操作建议。

你的任务：
1. 分析当前的市场趋势、支撑阻力位。
2. 结合当前的仓位（已使用 {pos_summary['used_units']}/100 份），决定是否需要买入、卖出或保持不动。
3. **强制要求**：你必须调用 `execute_trade` 执行交易，或者调用 `no_action` 确认今日不操作。
4. 如果你决定买入或卖出，请在 `conclusion` 中简要说明理由。如果你决定不操作，请在 `reason` 中简要说明理由。
5. 你的分析必须基于当前日期 {sim_date if sim_date else "最新数据"} 的信息。

请注意：预演模式下，你应该表现得像是在当天实时交易一样。
"""

            prompt = f"""
            **近期市场数据 (最近5个周期):**
            {json.dumps(hist_context, indent=2, ensure_ascii=False)}
            
            **仓位上下文与历史操作:**
            {pos_context}
            """

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            yield f"> 🧠 **AI 思考**: 正在审阅行情指标并评估交易机会 (模型: {self.model_name})...\n\n"

            # First call to check for tool usage
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            
            if msg.tool_calls:
                messages.append(msg)
                for tool_call in msg.tool_calls:
                    if tool_call.function.name == "execute_trade":
                        args = json.loads(tool_call.function.arguments)
                        action = args.get("action")
                        units = args.get("units")
                        conclusion = args.get("conclusion", "无理由")
                        
                        yield f"> ⚙️ **工具调用**: `execute_trade(action='{action}', units={units})`\n\n"
                        
                        # Execute the trade if pos_manager is provided
                        result_msg = ""
                        if pos_manager:
                            try:
                                # Use sim_date if in simulation mode, otherwise use real today
                                trade_date = sim_date if sim_date else datetime.now().strftime("%Y-%m-%d")
                                actual_units = units if action == "buy" else -units
                                pos_manager.add_record(symbol, trade_date, actual_units, latest_price, conclusion=conclusion)
                                result_msg = f"成功执行操作: {action} {units} 份, 价格 {latest_price:.2f} (日期: {trade_date})"
                            except Exception as e:
                                result_msg = f"操作失败: {str(e)}"
                        else:
                            result_msg = "错误：未配置仓位管理器，无法执行操作。"
                            
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "execute_trade",
                            "content": result_msg
                        })
                        yield f"> ✅ **执行结果**: {result_msg}\n\n"

                    elif tool_call.function.name == "no_action":
                        args = json.loads(tool_call.function.arguments)
                        reason = args.get("reason", "无需操作")
                        
                        yield f"> ⚙️ **工具调用**: `no_action(reason='{reason}')`\n\n"
                        
                        result_msg = ""
                        if pos_manager:
                            try:
                                trade_date = sim_date if sim_date else datetime.now().strftime("%Y-%m-%d")
                                pos_manager.add_record(symbol, trade_date, 0, latest_price, conclusion=reason)
                                result_msg = f"确认今日不操作。原因: {reason} (日期: {trade_date})"
                            except Exception as e:
                                result_msg = f"操作失败: {str(e)}"
                        else:
                            result_msg = "错误：未配置仓位管理器。"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "no_action",
                            "content": result_msg
                        })
                        yield f"> ✅ **执行结果**: {result_msg}\n\n"

                yield "> 📝 **正在生成分析报告**...\n\n"
                
                # Second call to get final report after tool execution
                final_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                )
                
                for chunk in final_response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                # No tool call, AI might have just replied with text (though we forced tool call in prompt)
                if msg.content:
                    yield msg.content
                else:
                    yield "AI 未做出决策且未返回内容。"

        except Exception as e:
            yield f"\n\n❌ **分析过程中发生错误**: {str(e)}\n"
            import traceback
            print(traceback.format_exc())

    def analyze_market(self, symbol: str, df: pd.DataFrame, pos_summary: dict = None):
        """Analyze market data using LLM or fallback to mock"""
        if df is None or df.empty:
            return "No data available for analysis."

        if not self.client:
            # Return a professional-looking mock report if no API key is provided
            return self._generate_mock_report(symbol, df)
        
        # Prepare a summary of the latest data
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        
        pos_context = ""
        if pos_summary and pos_summary.get("total_budget", 0) > 0:
            history_str = "\n".join([f"- {r['date']}: 购买 {r['units']} 份, 价格 {r['price']:.2f}" for r in pos_summary.get("history", [])])
            pos_context = f"""
        **仓位上下文信息:**
        - 总预算金额: {pos_summary['total_budget']} (划分为 100 份)
        - 已使用仓位: {pos_summary['used_units']}/100 份
        - 剩余可用仓位: {pos_summary['remaining_units']}/100 份
        - 历史购买记录:
        {history_str if history_str else "暂无记录"}
        """

        prompt = f"""
        你是一位专业的金融分析师。请分析以下 {symbol} 的市场数据，并结合当前的仓位状态给出今日的操作策略：
        
        **市场数据:**
        - 当前价格: {latest['Close']:.2f}
        - 价格涨跌幅 (上一周期): {price_change:.2f}%
        - RSI (14): {latest.get('RSI', 'N/A')}
        - MACD: {latest.get('MACD', 'N/A')}
        - 均线系统 (MA5/MA20/MA60): {latest.get('MA5', 'N/A')}/{latest.get('MA20', 'N/A')}/{latest.get('MA60', 'N/A')}
        
        {pos_context}
        
        请提供以下内容的中文报告：
        1. 当前趋势的简要总结（看涨/看跌/震荡）。
        2. 关键技术指标解读。
        3. **今日仓位策略决策**: 结合当前剩余仓位和市场走势，建议今日是 增仓、减仓 还是 持仓不动？如果增减仓，建议操作多少份 (0-100份)？
        4. 潜在的支撑位与阻力位。
        5. 对未来几个周期的简洁展望。
        
        要求：专业、简洁、直接。请使用 Markdown 格式。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的金融市场分析助手，专门负责提供深度、准确的行情分析。请始终使用中文回答。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Analysis failed: {str(e)}\n\nFallback to Mock Report:\n\n" + self._generate_mock_report(symbol, df)
