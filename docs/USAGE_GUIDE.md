# Stock Hub 使用指南

> 量化交易一体化平台完整使用文档

---

## 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [后端使用](#后端使用)
4. [前端使用](#前端使用)
5. [API 接口](#api-接口)
6. [数据采集](#数据采集)
7. [因子研究](#因子研究)
8. [信号管理](#信号管理)
9. [AI 分析](#ai-分析)
10. [消息推送](#消息推送)
11. [Agent 问股](#agent-问股)
12. [常见问题](#常见问题)

---

## 快速开始

### 1. 克隆项目

```bash
cd D:\githbu
git clone <repository-url> stock-hub
cd stock-hub
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置（至少配置一个 AI API Key）
notepad .env  # Windows
# vim .env    # Linux/Mac
```

### 5. 初始化数据

```bash
stock-hub init
```

### 6. 启动服务

```bash
# 启动后端
stock-hub serve

# 新终端启动前端
cd frontend
npm install
npm run dev
```

### 7. 访问

- **API 文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:3000

---

## 环境配置

### .env 配置说明

```bash
# ========== 应用配置 ==========
APP_NAME=Stock Hub
APP_VERSION=0.1.0
DEBUG=true                    # 开发环境设为 true

# ========== 数据目录 ==========
DATA_DIR=./data
LOG_DIR=./logs

# ========== AI 模型配置（至少配置一个）==========
# OpenAI
AI_PROVIDER=openai
AI_API_KEY=sk-xxx             # 你的 API Key
AI_MODEL=gpt-4
AI_BASE_URL=                  # 可选，自定义 API 地址

# 其他 AI 提供商（可选）
# AI_PROVIDER=claude
# AI_API_KEY=sk-ant-xxx

# AI_PROVIDER=deepseek
# AI_API_KEY=sk-xxx

# AI_PROVIDER=qwen
# AI_API_KEY=sk-xxx

# AI_PROVIDER=gemini
# AI_API_KEY=AIzaSyxxx

# ========== 数据源配置 ==========
DATA_PROVIDER=akshare         # akshare/tushare/yfinance
TUSHARE_TOKEN=                # Tushare 需要

# ========== 通知渠道配置（可选）==========
# 企业微信
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 飞书
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID=123456789

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx

# ========== 执行配置（实盘时配置）==========
GATEWAY_TYPE=sim              # sim/ctp/stock
CTP_BROKER_ID=
CTP_USER_ID=
CTP_PASSWORD=

# ========== 风控配置 ==========
MAX_POSITION_RATIO=0.3        # 最大持仓比例
MAX_DAILY_LOSS=0.05           # 最大日亏损
MAX_DRAWDOWN=0.1              # 最大回撤
```

### AI 模型配置示例

#### OpenAI

```bash
AI_PROVIDER=openai
AI_API_KEY=sk-xxxxxxxxxxxx
AI_MODEL=gpt-4
```

#### DeepSeek

```bash
AI_PROVIDER=deepseek
AI_API_KEY=sk-xxxxxxxxxxxx
AI_MODEL=deepseek-chat
```

#### 通义千问

```bash
AI_PROVIDER=qwen
AI_API_KEY=sk-xxxxxxxxxxxx
AI_MODEL=qwen-turbo
```

---

## 后端使用

### CLI 命令

```bash
# 启动服务
stock-hub serve [--host 0.0.0.0] [--port 8000] [--reload]

# 初始化数据目录
stock-hub init

# 同步数据
stock-hub sync --market A --symbols 600519,000858
```

### 启动选项

```bash
# 默认启动
stock-hub serve

# 指定端口
stock-hub serve --port 8001

# 开启热重载（开发模式）
stock-hub serve --reload

# 指定监听地址
stock-hub serve --host 127.0.0.1
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_config.py

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=src
```

---

## 前端使用

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 页面说明

| 页面 | 路由 | 功能 |
|------|------|------|
| 工作台 | `/` | 查看概览、持仓、最新信号 |
| 股票列表 | `/stocks` | 浏览股票、查看详情 |
| 分析报告 | `/analysis` | 使用 AI 分析股票 |
| 信号管理 | `/signals` | 查看、审批信号 |
| 持仓管理 | `/portfolio` | 查看持仓和盈亏 |
| 新闻舆情 | `/news` | 浏览新闻、查看舆情 |
| 设置 | `/settings` | 配置 AI 模型、数据源 |

---

## API 接口

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **API 文档**: `http://localhost:8000/docs`（Swagger UI）
- **格式**: JSON

### 股票相关

#### 获取股票列表

```bash
curl http://localhost:8000/api/v1/stocks
```

```bash
# 按市场过滤
curl http://localhost:8000/api/v1/stocks?market=A
```

#### 获取股票详情

```bash
curl http://localhost:8000/api/v1/stocks/600519?market=A
```

#### 获取 K 线数据

```bash
curl "http://localhost:8000/api/v1/stocks/600519/kline?market=A&start_date=2026-01-01&end_date=2026-06-01"
```

#### 获取技术指标

```bash
curl http://localhost:8000/api/v1/stocks/600519/technical?market=A
```

### 分析相关

#### 分析股票

```bash
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "market": "A",
    "strategy": "comprehensive"
  }'
```

#### 获取策略列表

```bash
curl http://localhost:8000/api/v1/analysis/strategies
```

### 信号相关

#### 创建信号

```bash
curl -X POST http://localhost:8000/api/v1/signals \
  -H "Content-Type: application/json" \
  -d '{
    "targets": {
      "600519.SSE": 0.08,
      "000858.SZE": 0.07
    },
    "source": "manual"
  }'
```

#### 审批信号

```bash
curl -X POST http://localhost:8000/api/v1/signals/{signal_id}/approve
```

#### 拒绝信号

```bash
curl -X POST "http://localhost:8000/api/v1/signals/{signal_id}/reject?reason=风控拒绝"
```

### Agent 相关

#### Agent 对话

```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析一下贵州茅台"
  }'
```

#### Agent 分析

```bash
curl "http://localhost:8000/api/v1/agent/analyze?symbol=600519&strategy=comprehensive"
```

### 新闻相关

#### 获取新闻

```bash
curl "http://localhost:8000/api/v1/news?symbol=600519&market=A&days=7"
```

#### 获取舆情

```bash
curl "http://localhost:8000/api/v1/news/sentiment?symbol=600519&market=A&days=30"
```

---

## 数据采集

### 支持的数据源

| 数据源 | 市场 | 说明 |
|--------|------|------|
| AkShare | A股/港股 | 接入方便；商用前须核验 AKShare 及其上游数据源授权 |
| Tushare | A股 | 需要注册获取 Token；个人/非商业权限不等于商业数据授权 |
| YFinance | 港股/美股 | 免费 |

> 数据源的许可证、服务条款和市场数据权利独立于本项目许可。商用部署、再分发或对外提供数据服务前，须分别取得相应权利；详见仓库根目录的[第三方声明](../THIRD_PARTY_NOTICES.md)。

### 同步数据

```bash
# 同步单只股票
stock-hub sync --market A --symbols 600519

# 同步多只股票
stock-hub sync --market A --symbols 600519,000858,601318

# 同步港股
stock-hub sync --market HK --symbols 00700,09988
```

### 数据存储

数据存储在 `data/` 目录：

```
data/
├── catalog/          # 标的目录
│   └── instruments.json
├── daily/            # 日线数据
│   ├── A/           # A股
│   │   ├── 600519.parquet
│   │   └── ...
│   └── HK/          # 港股
│       ├── 00700.parquet
│       └── ...
└── cache/            # 缓存
```

---

## 因子研究

### 内置因子

| 因子 | 名称 | 类别 | 说明 |
|------|------|------|------|
| ma5 | 5日均线 | ma | 5日移动平均 |
| ma10 | 10日均线 | ma | 10日移动平均 |
| ma20 | 20日均线 | ma | 20日移动平均 |
| ma60 | 60日均线 | ma | 60日移动平均 |
| volume_ratio | 量比 | volume | 成交量比率 |
| price_change | 涨跌幅 | price | 价格变化率 |
| volatility | 波动率 | risk | 价格波动率 |

### 使用因子

```python
from src.research import create_default_registry

# 创建因子注册表
registry = create_default_registry()

# 列出所有因子
factors = registry.list_factors()

# 按类别列出
ma_factors = registry.list_by_category("ma")

# 计算因子
import pandas as pd
df = pd.read_parquet("data/daily/A/600519.parquet")
result = registry.calculate("ma5", df)
```

### 自定义因子

```python
from src.research import FactorRegistry

registry = FactorRegistry()

# 定义因子函数
def my_factor(df):
    return df["close"] / df["close"].rolling(20).mean()

# 注册因子
registry.register(
    name="my_factor",
    func=my_factor,
    description="自定义因子",
    category="custom"
)
```

---

## 信号管理

### 信号生命周期

```
draft → approved → published → consumed → archived
         ↓
      rejected
```

### 创建信号

```python
from src.research import ResearchService

service = ResearchService()

# 创建信号
signal = service.create_signal(
    targets={
        "600519.SSE": 0.08,
        "000858.SZE": 0.07,
    },
    source="manual",
)

# 验证信号
is_valid, issues = service.validate_signal(signal)

# 审批信号
approved = service.approve_signal(signal)

# 发布信号
published = service.publish_signal(approved)
```

### 信号格式

```json
{
  "schema_version": "v1",
  "signal_id": "uuid",
  "as_of": "2026-06-05T18:00:00",
  "source": "manual",
  "status": "published",
  "targets": {
    "600519.SSE": 0.08,
    "000858.SZE": 0.07
  },
  "cash_weight": 0.85,
  "risk_overlay": {
    "max_single_name_weight": 0.1,
    "max_gross_leverage": 1.0
  }
}
```

---

## AI 分析

### 支持的策略

| 策略 | 名称 | 说明 |
|------|------|------|
| comprehensive | 综合分析 | 技术面+基本面综合分析 |
| ma_cross | 均线金叉 | MA5/MA10/MA20 金叉判断 |
| macd | MACD | MACD 金叉/死叉判断 |
| trend | 趋势分析 | 多头/空头趋势判断 |
| wave | 波浪理论 | 波浪形态识别 |
| chan | 缠论 | 中枢和买卖点识别 |
| news | 新闻事件 | 新闻情绪分析 |
| hot | 热点题材 | 市场热点判断 |
| growth | 成长质量 | 营收/利润增长分析 |
| value | 价值投资 | PE/PB 估值分析 |

### 使用分析

```python
from src.analysis import AnalysisService, AIModelFactory
from src.config import get_settings

# 创建服务
config = get_settings()
ai_adapter = AIModelFactory.create(config)
service = AnalysisService(ai_adapter)

# 分析股票
result = await service.analyze_stock("600519", "comprehensive")

print(f"评分: {result.score}")
print(f"信号: {result.signal}")
print(f"趋势: {result.trend}")
print(f"理由: {result.reason}")
```

---

## 消息推送

### 支持的渠道

| 渠道 | 配置项 | 说明 |
|------|--------|------|
| 企业微信 | WECHAT_WEBHOOK | Webhook 方式 |
| 飞书 | FEISHU_WEBHOOK | Webhook 方式 |
| Telegram | TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID | Bot 方式 |
| Discord | DISCORD_WEBHOOK_URL | Webhook 方式 |

### 使用推送

```python
from src.analysis.notification import NotificationManager
from src.config import get_settings

# 创建管理器
config = get_settings()
manager = NotificationManager(config)

# 推送消息
await manager.push("测试消息")

# 推送到指定渠道
await manager.push("测试消息", channels=["wechat", "telegram"])
```

---

## Agent 问股

### 使用方式

#### 1. API 调用

```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "分析一下贵州茅台的技术面"}'
```

#### 2. WebSocket 连接

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/agent/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({ message: '你好' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

#### 3. Python 调用

```python
from src.analysis import StockAgent

agent = StockAgent()

# 对话
response = await agent.chat("session-1", "分析一下贵州茅台")

# 策略分析
result = await agent.analyze_with_strategy("600519", "comprehensive")
```

---

## 常见问题

### Q: 如何配置 AI API Key？

A: 编辑 `.env` 文件，配置 `AI_PROVIDER` 和 `AI_API_KEY`：

```bash
AI_PROVIDER=openai
AI_API_KEY=sk-xxxxxxxxxxxx
```

### Q: 如何添加自定义股票到监控列表？

A: 使用 Python API：

```python
from src.data import DataService

service = DataService()
service.add_to_watchlist("601318", {
    "vt_symbol": "601318.SSE",
    "name": "中国平安",
    "market": "A",
    "lot_size": 100,
})
```

### Q: 数据同步失败怎么办？

A: 检查以下几点：
1. 网络连接是否正常
2. 数据源是否可用
3. 查看日志文件 `logs/` 目录

### Q: 如何切换 AI 模型？

A: 修改 `.env` 文件：

```bash
# 切换到 DeepSeek
AI_PROVIDER=deepseek
AI_API_KEY=sk-xxxxxxxxxxxx
AI_MODEL=deepseek-chat
```

然后重启服务。

### Q: 如何运行回测？

A: 目前回测功能待实现，可以使用 API 创建信号进行测试：

```bash
curl -X POST http://localhost:8000/api/v1/signals \
  -H "Content-Type: application/json" \
  -d '{
    "targets": {"600519.SSE": 0.1},
    "source": "manual"
  }'
```

### Q: 如何查看日志？

A: 日志文件在 `logs/` 目录：

```bash
# 查看最新日志
tail -f logs/stock-hub.log
```

### Q: 如何部署到生产环境？

A: 参考以下步骤：

```bash
# 1. 设置环境变量
export DEBUG=false

# 2. 配置生产数据库（可选）

# 3. 启动服务
stock-hub serve --host 0.0.0.0 --port 8000

# 4. 使用 Nginx 反向代理（可选）
```

---

## 技术支持

- **文档**: `docs/` 目录
- **API 文档**: http://localhost:8000/docs
- **测试**: `pytest`

---

## 更新日志

### v0.1.0 (2026-06-05)

- 初始版本
- 完成基础架构
- 完成数据层
- 完成研究层
- 完成执行层
- 完成分析层
- 完成新闻层
- 完成 Web 层
- 完成契约层
