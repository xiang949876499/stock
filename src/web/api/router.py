"""API 路由"""

from fastapi import APIRouter

from .stocks import router as stocks_router
from .analysis import router as analysis_router
from .signals import router as signals_router
from .execution import router as execution_router
from .backtest import router as backtest_router
from .news import router as news_router
from .agent import router as agent_router
from .recommend import router as recommend_router
from .plugins import router as plugins_router
from .commands import router as commands_router
from .connectors import router as connectors_router

router = APIRouter(prefix="/api/v1")

# 注册子路由
router.include_router(stocks_router)
router.include_router(analysis_router)
router.include_router(signals_router)
router.include_router(execution_router)
router.include_router(backtest_router)
router.include_router(news_router)
router.include_router(agent_router)
router.include_router(recommend_router)
router.include_router(plugins_router)
router.include_router(commands_router)
router.include_router(connectors_router)


@router.get("/")
async def root():
    """API 根路径"""
    return {"message": "Stock Hub API v1"}
