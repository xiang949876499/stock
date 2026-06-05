"""应用入口"""

import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import Settings, get_settings
from src.infra.logger import setup_logger, get_logger
from src.infra.scheduler import TaskScheduler
from src.web.api.router import router as api_router

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

# 注册路由
app.include_router(api_router)

# 全局变量
settings: Settings = None
logger = None
scheduler: TaskScheduler = None


@app.on_event("startup")
async def startup():
    """应用启动"""
    global settings, logger, scheduler

    # 加载配置
    settings = get_settings()

    # 设置日志
    logger = setup_logger("stock-hub", settings.log_dir)
    logger.info("应用启动", version=settings.app_version)

    # 启动调度器
    scheduler = TaskScheduler()
    scheduler.setup()
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    """应用关闭"""
    global scheduler
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
@click.option("--port", default=8000, type=int, help="监听端口")
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
    # 创建数据目录
    import os
    os.makedirs("./data/catalog", exist_ok=True)
    os.makedirs("./data/daily/A", exist_ok=True)
    os.makedirs("./data/daily/HK", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    click.echo("数据初始化完成")


@cli.command()
@click.option("--market", default="A", help="市场类型")
@click.option("--symbols", help="股票代码，逗号分隔")
def sync(market: str, symbols: str):
    """同步数据"""
    click.echo(f"同步数据: market={market}, symbols={symbols}")
    # TODO: 实现数据同步
    click.echo("数据同步完成")


if __name__ == "__main__":
    cli()
