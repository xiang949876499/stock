# Stock Hub

量化交易一体化平台

## 功能特性

- 多数据源聚合（A股/港股）
- 因子研究与模型训练（qlib）
- 信号生成与执行（vnpy）
- AI 分析报告
- 消息推送（企微/飞书/Telegram）
- Web 工作台

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/stock-hub.git
cd stock-hub

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
vim .env
```

### 运行

```bash
# 初始化数据
stock-hub init

# 启动服务
stock-hub serve

# 运行测试
pytest
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src tests

# 代码检查
ruff check src tests
```

## License

MIT

## TradingAgents

Optional multi-agent stock analysis is available through the `tradingagents` strategy. See `docs/tradingagents.md` for install, configuration, and API usage.

Simulated trading can also use optional Kronos forecast summaries during the daily optimization step. Install the `kronos` extra and keep `../Kronos` available when enabling real model inference; see `docs/tradingagents.md` for the candidate snapshot format and runtime knobs.

## Docker

Build and run the API container:

```bash
docker build -t stock-hub:latest .
docker compose up -d
```

The API is exposed on `http://localhost:8080`, and the frontend is exposed on `http://localhost:3000`.

The compose file maps `./data` to `/app/data`, so daily simulation optimization reports are saved on the host under `data/simulation_reviews/YYYY-MM-DD/`.
