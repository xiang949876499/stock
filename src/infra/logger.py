"""日志系统"""

import logging
import structlog
from pathlib import Path


def setup_logger(
    name: str,
    log_dir: str = "./logs",
    level: int = logging.INFO,
) -> structlog.BoundLogger:
    """设置日志"""
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(name)


def get_logger(name: str) -> structlog.BoundLogger:
    """获取日志"""
    return structlog.get_logger(name)
