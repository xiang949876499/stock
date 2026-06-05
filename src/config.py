"""配置管理"""

from pathlib import Path
from typing import Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    app_name: str = "Stock Hub"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据目录
    data_dir: str = "./data"
    log_dir: str = "./logs"

    # AI 模型
    ai_provider: str = "openai"  # openai/claude/deepseek/qwen/gemini
    ai_api_key: str = ""
    ai_model: str = "gpt-4"
    ai_base_url: Optional[str] = None

    # 数据源
    data_provider: str = "akshare"  # akshare/tushare/yfinance
    tushare_token: Optional[str] = None

    # 通知
    wechat_webhook: Optional[str] = None
    feishu_webhook: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook: Optional[str] = None

    # 执行
    gateway_type: str = "sim"  # sim/ctp/stock
    ctp_broker_id: Optional[str] = None
    ctp_user_id: Optional[str] = None
    ctp_password: Optional[str] = None

    # 风控
    max_position_ratio: float = 0.3
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_yaml_config(config_path: Path) -> dict:
    """加载 YAML 配置文件"""
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config or {}


def get_settings() -> Settings:
    """获取应用配置"""
    return Settings()
