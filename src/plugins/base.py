"""插件基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from src.infra.logger import get_logger
from src.plugins.cache import plugin_cache
from src.plugins.errors import handle_plugin_error

logger = get_logger(__name__)


class AnalysisPlugin(ABC):
    """分析插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @abstractmethod
    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析

        Args:
            stock_data: 股票数据
            params: 分析参数

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义

        Returns:
            参数定义字典，格式:
            {
                "param_name": {
                    "type": "int|float|str|List[str]",
                    "default": ...,
                    "description": "..."
                }
            }
        """
        pass

    async def safe_execute(
        self,
        stock_data: Any,
        params: Dict[str, Any],
        cache_ttl: int = 300
    ) -> Dict[str, Any]:
        """安全执行分析（带缓存和错误处理）

        Args:
            stock_data: 股票数据
            params: 分析参数
            cache_ttl: 缓存过期时间（秒），默认 300 秒

        Returns:
            分析结果字典，错误时返回包含 error 信息的字典
        """
        # 生成缓存键
        cache_key = f"{self.name}:{str(stock_data)}:{str(params)}"

        # 尝试获取缓存
        cached_result = plugin_cache.get(cache_key)
        if cached_result is not None:
            logger.debug("plugin_cache_hit", plugin=self.name)
            return cached_result

        # 执行插件
        try:
            logger.info("plugin_execution_start", plugin=self.name, params=params)
            result = await self.execute(stock_data, params)

            # 缓存结果
            plugin_cache.set(cache_key, result)
            logger.info("plugin_execution_success", plugin=self.name)

            return result
        except Exception as e:
            logger.error("plugin_execution_failed", plugin=self.name, error=str(e))
            return handle_plugin_error(e, self.name, params)
