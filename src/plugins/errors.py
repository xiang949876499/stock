"""插件错误处理"""

import traceback
from typing import Dict, Any
from src.infra.logger import get_logger

logger = get_logger(__name__)


class PluginError(Exception):
    """插件错误基类"""
    pass


class DataNotFoundError(PluginError):
    """数据未找到错误"""
    pass


class InvalidParameterError(PluginError):
    """无效参数错误"""
    pass


class CalculationError(PluginError):
    """计算错误"""
    pass


def handle_plugin_error(error: Exception, plugin_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """处理插件错误"""
    error_type = type(error).__name__
    error_msg = str(error)

    logger.error(
        "plugin_execution_error",
        plugin=plugin_name,
        error_type=error_type,
        error_message=error_msg,
        params=params,
        traceback=traceback.format_exc()
    )

    return {
        "error": True,
        "error_type": error_type,
        "error_message": error_msg,
        "plugin": plugin_name
    }
