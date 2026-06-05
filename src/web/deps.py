"""依赖注入"""

from functools import lru_cache

from src.config import Settings, get_settings
from src.data.service import DataService
from src.research.service import ResearchService
from src.execution.service import ExecutionService
from src.analysis.service import AnalysisService
from src.analysis.ai.factory import AIModelFactory
from src.news.service import NewsService


@lru_cache()
def get_data_service() -> DataService:
    """获取数据服务"""
    return DataService()


@lru_cache()
def get_research_service() -> ResearchService:
    """获取研究服务"""
    return ResearchService()


@lru_cache()
def get_execution_service() -> ExecutionService:
    """获取执行服务"""
    return ExecutionService()


@lru_cache()
def get_analysis_service() -> AnalysisService:
    """获取分析服务"""
    config = get_settings()
    ai_adapter = AIModelFactory.create(config)
    return AnalysisService(ai_adapter)


@lru_cache()
def get_news_service() -> NewsService:
    """获取新闻服务"""
    return NewsService()
