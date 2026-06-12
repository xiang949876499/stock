"""应用入口"""

import os
# 禁用代理访问国内数据源（必须在其他导入之前）
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings, get_settings
from src.infra.logger import setup_logger, get_logger
from src.infra.scheduler import TaskScheduler
from src.trading.scheduler import TradingScheduler
from src.web.api.router import router as api_router
from src.web.middleware.error_handler import stockhub_exception_handler, generic_exception_handler
from src.exceptions import StockHubException

# 集成适配器
from src.integrations.registry import registry
from src.integrations.backtrader.adapter import BacktraderAdapter
from src.integrations.easytrader.adapter import EasytraderAdapter
from src.integrations.qbot.adapter import QbotAdapter
from src.integrations.ai_quant.adapter import AIQuantAdapter

# 创建 FastAPI 应用
app = FastAPI(
    title="Stock Hub API",
    description="量化交易一体化平台",
    version="0.1.0",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(StockHubException, stockhub_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 注册路由
app.include_router(api_router)

# 全局变量
settings: Settings = None
logger = None
scheduler: TaskScheduler = None
trading_scheduler: TradingScheduler = None


def register_integrations():
    """注册所有集成适配器"""
    registry.register(BacktraderAdapter(enabled=True))
    registry.register(EasytraderAdapter(broker="ths", enabled=True))
    registry.register(QbotAdapter(enabled=True))
    registry.register(AIQuantAdapter(enabled=True))


@app.on_event("startup")
async def startup():
    """应用启动"""
    global settings, logger, scheduler, trading_scheduler

    # 加载配置
    settings = get_settings()

    # 设置日志
    logger = setup_logger("stock-hub", settings.log_dir)
    logger.info("应用启动", version=settings.app_version)

    # 注册并初始化集成适配器
    register_integrations()
    await registry.initialize_all()

    # 自动刷新股票目录（如果超过 24 小时未更新）
    try:
        from src.data.catalog.manager import InstrumentCatalog
        from src.data.providers.akshare_provider import AkShareProvider
        catalog = InstrumentCatalog()
        if catalog.needs_refresh(max_age_hours=24):
            logger.info("股票目录需要刷新，开始后台同步...")
            provider = AkShareProvider()
            await catalog.refresh_from_provider(provider)
    except Exception as e:
        logger.warning(f"自动刷新股票目录失败: {e}")

    # 启动调度器
    scheduler = TaskScheduler()
    scheduler.setup()
    scheduler.start()

    # 初始化模拟交易（使用全局单例引擎）
    from src.web.api.trading import get_engine
    engine = get_engine()
    engine.start()  # 启动引擎，允许调度器执行分析
    trading_scheduler = TradingScheduler()
    trading_scheduler.setup(engine)
    trading_scheduler.start()
    logger.info("模拟交易调度器启动")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭"""
    global scheduler, trading_scheduler
    if trading_scheduler:
        trading_scheduler.stop()
    if scheduler:
        scheduler.stop()
    if logger:
        logger.info("应用关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Stock Hub API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@click.group()
def cli():
    """Stock Hub CLI"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8080, type=int, help="监听端口")
@click.option("--reload", is_flag=True, help="自动重载")
def serve(host: str, port: int, reload: bool):
    """启动服务"""
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def init():
    """初始化数据"""
    click.echo("初始化数据...")
    import os
    os.makedirs("./data/catalog", exist_ok=True)
    os.makedirs("./data/daily/A", exist_ok=True)
    os.makedirs("./data/daily/HK", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    click.echo("数据初始化完成")


@cli.command()
def sync_catalog():
    """同步全量股票目录（A股+港股）"""
    import asyncio

    async def _sync():
        from src.data.catalog.manager import InstrumentCatalog
        from src.data.providers.akshare_provider import AkShareProvider

        click.echo("正在获取全量股票列表...")
        provider = AkShareProvider()
        catalog = InstrumentCatalog()

        await catalog.refresh_from_provider(provider)

        a_count = sum(1 for v in catalog.mapping.values() if v.get("market") == "A")
        hk_count = sum(1 for v in catalog.mapping.values() if v.get("market") == "HK")
        click.echo(f"同步完成: A股 {a_count} 只, 港股 {hk_count} 只, 共 {len(catalog.mapping)} 只")

    asyncio.run(_sync())


@cli.command()
@click.option("--market", default="A", help="市场类型")
@click.option("--symbols", help="股票代码，逗号分隔")
def sync(market: str, symbols: str):
    """同步数据"""
    click.echo(f"同步数据: market={market}, symbols={symbols}")
    # TODO: 实现数据同步
    click.echo("数据同步完成")


@cli.command()
@click.option("--market", default="A", help="市场类型 (A/HK)")
@click.option("--top", default=10, type=int, help="推荐数量")
@click.option("--analyze", is_flag=True, help="是否进行 AI 分析")
def recommend(market: str, top: int, analyze: bool):
    """推荐股票"""
    import asyncio

    async def _recommend():
        from src.analysis.strategies.stock_picker import get_stock_recommendations
        from src.analysis.service import AnalysisService
        from src.analysis.ai.factory import AIModelFactory
        from src.config import get_settings

        click.echo(f"正在推荐 {market} 市场 Top {top} 股票...")

        # 获取推荐
        recommendations = await get_stock_recommendations(market, top)

        if not recommendations:
            click.echo("没有找到推荐股票")
            return

        if analyze:
            # AI 分析
            config = get_settings()
            ai_adapter = AIModelFactory.create(config)

            if not ai_adapter:
                click.echo("AI 未配置，仅显示技术评分")
                for i, stock in enumerate(recommendations, 1):
                    click.echo(f"{i}. {stock['symbol']} - {stock['name']} | 技术评分: {stock['score']:.1f}")
                return

            service = AnalysisService(ai_adapter)

            click.echo("\n正在进行 AI 分析...\n")
            click.echo(f"{'序号':<4} {'代码':<10} {'名称':<10} {'技术分':<8} {'AI分':<8} {'信号':<8} {'趋势':<8}")
            click.echo("-" * 70)

            for i, stock in enumerate(recommendations, 1):
                try:
                    analysis = await service.analyze_stock(stock["symbol"], "comprehensive")
                    click.echo(
                        f"{i:<4} {stock['symbol']:<10} {stock['name']:<10} "
                        f"{stock['score']:<8.1f} {analysis.score:<8.1f} "
                        f"{analysis.signal:<8} {analysis.trend:<8}"
                    )
                except Exception as e:
                    click.echo(
                        f"{i:<4} {stock['symbol']:<10} {stock['name']:<10} "
                        f"{stock['score']:<8.1f} {'N/A':<8} {'N/A':<8} {'N/A':<8}"
                    )
        else:
            # 仅显示技术评分
            click.echo(f"\n{'序号':<4} {'代码':<10} {'名称':<10} {'技术评分':<10}")
            click.echo("-" * 40)

            for i, stock in enumerate(recommendations, 1):
                click.echo(
                    f"{i:<4} {stock['symbol']:<10} {stock['name']:<10} {stock['score']:<10.1f}"
                )

    asyncio.run(_recommend())


@cli.command()
@click.argument("symbol")
@click.option("--market", default="A", help="市场类型 (A/HK)")
@click.option("--strategy", default="comprehensive", help="分析策略")
def evaluate(symbol: str, market: str, strategy: str):
    """评估单只股票"""
    import asyncio

    async def _evaluate():
        from src.analysis.service import AnalysisService
        from src.analysis.ai.factory import AIModelFactory
        from src.config import get_settings

        click.echo(f"正在评估 {symbol}...")

        config = get_settings()
        ai_adapter = AIModelFactory.create(config)

        if not ai_adapter:
            click.echo("错误: AI 未配置，请在 .env 中设置 AI_API_KEY")
            return

        service = AnalysisService(ai_adapter)

        try:
            result = await service.analyze_stock(symbol, strategy)

            click.echo(f"\n{'='*50}")
            click.echo(f"股票: {symbol}")
            click.echo(f"{'='*50}")
            click.echo(f"评分: {result.score:.1f}/100")
            click.echo(f"信号: {result.signal}")
            click.echo(f"趋势: {result.trend}")
            click.echo(f"{'='*50}")
            click.echo(f"分析理由:")
            click.echo(result.reason)
            click.echo(f"{'='*50}")

        except Exception as e:
            click.echo(f"评估失败: {e}")

    asyncio.run(_evaluate())


if __name__ == "__main__":
    cli()
