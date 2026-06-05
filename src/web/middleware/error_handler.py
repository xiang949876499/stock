"""错误处理中间件"""

from fastapi import Request
from fastapi.responses import JSONResponse

from src.exceptions import StockHubException
from src.infra.logger import get_logger

logger = get_logger("error_handler")


async def stockhub_exception_handler(request: Request, exc: StockHubException) -> JSONResponse:
    """Stock Hub 异常处理"""
    logger.error(
        f"请求错误: {request.method} {request.url.path}",
        code=exc.code,
        message=exc.message,
    )
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理"""
    logger.error(
        f"未处理的异常: {request.method} {request.url.path}",
        error=str(exc),
        exc_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "服务器内部错误",
            }
        },
    )
