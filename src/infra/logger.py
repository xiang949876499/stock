"""日志系统"""

import logging
import structlog
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))


def _cst_timestamper(logger, method_name, event_dict):
    """使用北京时间的日志时间戳处理器"""
    event_dict["timestamp"] = datetime.now(CST).isoformat()
    return event_dict


# 模块加载时就配置好，避免缓存问题
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        _cst_timestamper,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def setup_logger(
    name: str,
    log_dir: str = "./logs",
    level: int = logging.INFO,
) -> structlog.BoundLogger:
    """设置日志"""
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    return structlog.get_logger(name)


def get_logger(name: str) -> structlog.BoundLogger:
    """获取日志"""
    return structlog.get_logger(name)
