"""代理基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.plugins.base import AnalysisPlugin


class AnalysisAgent(ABC):
    """分析代理基类

    代理封装复杂的分析工作流，协调多个插件和 AI 适配器完成分析任务。
    """

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        """初始化代理

        Args:
            ai_adapter: AI 模型适配器（可选）
            plugins: 代理使用的插件列表
        """
        self.ai_adapter = ai_adapter
        self.plugins: List[AnalysisPlugin] = plugins if plugins is not None else []

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """系统提示词，定义代理的角色和行为"""
        pass

    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """运行代理工作流

        默认工作流:
        1. 解析用户意图
        2. 执行相关插件
        3. 生成分析报告

        Args:
            query: 用户查询
            context: 额外上下文信息

        Returns:
            分析结果字典，包含 report 和 plugin_results
        """
        context = context or {}

        # Step 1: 解析意图
        intent = await self._parse_intent(query, context)

        # Step 2: 执行插件
        plugin_results = await self._execute_plugins(intent, context)

        # Step 3: 生成报告
        report = await self._generate_report(query, plugin_results, context)

        return {
            "query": query,
            "intent": intent,
            "plugin_results": plugin_results,
            "report": report,
        }

    async def _parse_intent(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析用户意图

        子类可覆盖此方法以实现自定义意图解析。

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            意图信息字典
        """
        return {"query": query, "plugins": [p.name for p in self.plugins]}

    async def _execute_plugins(
        self, intent: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行插件

        Args:
            intent: 解析后的意图
            context: 上下文信息

        Returns:
            各插件执行结果
        """
        results = {}
        stock_data = context.get("stock_data")
        params = context.get("params", {})

        for plugin in self.plugins:
            if plugin.name in intent.get("plugins", []):
                try:
                    result = await plugin.execute(stock_data, params)
                    results[plugin.name] = result
                except Exception as e:
                    results[plugin.name] = {"error": str(e)}

        return results

    async def _generate_report(
        self,
        query: str,
        plugin_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """生成分析报告

        子类可覆盖此方法以实现自定义报告生成。

        Args:
            query: 原始查询
            plugin_results: 插件执行结果
            context: 上下文信息

        Returns:
            分析报告文本
        """
        return f"分析完成，共执行 {len(plugin_results)} 个插件。"
