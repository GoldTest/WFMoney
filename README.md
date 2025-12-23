# WFMoney - 智能投资助手

WFMoney 是一款基于人工智能的金融行情分析与交易预演系统。它集成了实时数据获取、AI 智能策略分析以及回测预演功能，旨在帮助用户通过 AI 辅助决策提升投资效率。

## ✨ 核心功能

- **🚀 实时行情分析**：集成 yfinance 与 akshare，支持美股、A股、指数及加密货币的实时行情与技术指标显示。
- **🤖 AI 智能决策**：对接主流大模型（如 Gemini, OpenAI 等），根据市场数据、技术指标（SMA, RSI, MACD）提供买卖建议。
- **📅 历史回测预演**：支持选择历史日期进行逐日模拟演练，AI 自动根据当日收盘数据做出决策，并记录模拟持仓盈亏。
- **📊 智能持仓管理**：自动计算持仓成本、浮动盈亏及收益率，支持 100 股起步的真实仓位管理逻辑。
- **📝 决策日志回溯**：完整记录 AI 的每一条决策建议及其背后的逻辑理由（Conclusion & Reason）。

## 🛠️ 技术栈

- **后端**: Python, FastAPI, Uvicorn, Pandas
- **前端**: HTML5, JavaScript (ES6+), Tailwind CSS, Lightweight Charts
- **数据源**: yfinance, akshare, Binance API
- **AI 引擎**: OpenAI API 兼容接口

## 🚀 快速启动 (Windows)

项目已内置一键启动脚本，无需复杂配置：

1. **环境准备**：确保已安装 Python 3.8+。
2. **双击启动**：在项目根目录下双击 `start.bat` 文件。
3. **自动运行**：脚本将自动：
    - 检查并安装所需的 Python 依赖。
    - 启动后端 API 服务 (Port 8000)。
    - 启动前端 Web 服务 (Port 8080)。
    - 自动在默认浏览器中打开应用界面。

## 📂 项目结构

```text
ChatWithTrea/
├── backend/            # Python 后端逻辑
│   ├── ai_analyzer.py      # AI 分析核心逻辑
│   ├── position_manager.py # 持仓管理与盈亏计算
│   ├── utils.py            # 数据获取与指标计算工具
│   ├── main.py             # FastAPI 路由入口
│   └── config.py           # 持久化数据路径配置
├── frontend/           # 前端 Web 界面
│   └── index.html          # 单页面 Dashboard 界面
├── start.bat           # Windows 一键启动脚本
├── requirements.txt    # Python 依赖列表
└── .gitignore          # Git 忽略配置
```

## 🔒 数据隐私

所有持久化数据（如 AI 配置、持仓记录等）均存储在本地 Windows 系统的 `%LOCALAPPDATA%\WFMoney` 目录下，不会上传到除您配置的 AI API 以外的任何第三方服务器。

---

**免责声明**：本系统提供的所有分析结果仅供学习参考，不构成任何投资建议。投资有风险，入市需谨慎。
