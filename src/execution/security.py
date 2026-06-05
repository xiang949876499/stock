"""安全策略"""

import os
from pathlib import Path

from src.infra.logger import get_logger

logger = get_logger("security")


class SecurityViolation(Exception):
    """安全违规异常"""
    pass


class SecurityPolicy:
    """安全策略"""

    RED_LINES = [
        "LLM / MCP 工具不得直接调用 vnpy 发单 API",
        "MCP 与 Agent 配置中不得放置生产 CTP 密码",
        "生产密钥仅通过环境变量或本地加密配置注入",
        "llm_proposed 只能进入 draft，不得跳过 approved",
    ]

    @staticmethod
    def check_llm_direct_trade(llm_output: dict) -> bool:
        """检查 LLM 是否尝试直接交易"""
        if llm_output.get('status') not in ['draft', None]:
            raise SecurityViolation("LLM 输出必须是 draft 状态")
        return True

    @staticmethod
    def check_key_exposure(config: dict) -> bool:
        """检查密钥泄露"""
        sensitive_keys = ['ctp_password', 'api_key', 'secret_key']
        for key in sensitive_keys:
            if key in config and isinstance(config[key], str):
                if not config[key].startswith('${') and config[key]:
                    raise SecurityViolation(f"密钥 {key} 不能硬编码")
        return True


class KillSwitch:
    """紧急停止开关"""

    @staticmethod
    def check() -> bool:
        """检查是否应该停止交易"""
        # 环境变量检查
        if os.getenv('STOCK_HUB_EXECUTION_DISABLED') == '1':
            logger.warning("交易已通过环境变量禁用")
            return True

        # 文件开关检查
        stop_file = Path.home() / '.stock-hub' / 'STOP_TRADING'
        if stop_file.exists():
            logger.warning(f"交易已通过文件开关禁用: {stop_file}")
            return True

        return False
