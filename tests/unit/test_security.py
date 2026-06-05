"""安全策略测试"""

import pytest
import os
from pathlib import Path
from src.execution.security import SecurityPolicy, KillSwitch, SecurityViolation


def test_check_llm_direct_trade_draft():
    """测试 LLM 直接交易检查 - draft 状态"""
    llm_output = {"status": "draft", "targets": {"600519.SSE": 0.3}}
    assert SecurityPolicy.check_llm_direct_trade(llm_output) is True


def test_check_llm_direct_trade_published():
    """测试 LLM 直接交易检查 - published 状态"""
    llm_output = {"status": "published", "targets": {"600519.SSE": 0.3}}
    with pytest.raises(SecurityViolation):
        SecurityPolicy.check_llm_direct_trade(llm_output)


def test_check_key_exposure_safe():
    """测试密钥泄露检查 - 安全"""
    config = {"api_key": "${OPENAI_API_KEY}"}
    assert SecurityPolicy.check_key_exposure(config) is True


def test_check_key_exposure_hardcoded():
    """测试密钥泄露检查 - 硬编码"""
    config = {"api_key": "sk-1234567890"}
    with pytest.raises(SecurityViolation):
        SecurityPolicy.check_key_exposure(config)


def test_check_key_exposure_empty():
    """测试密钥泄露检查 - 空值"""
    config = {"api_key": ""}
    assert SecurityPolicy.check_key_exposure(config) is True


def test_kill_switch_env_disabled(monkeypatch):
    """测试环境变量禁用"""
    monkeypatch.setenv("STOCK_HUB_EXECUTION_DISABLED", "1")
    assert KillSwitch.check() is True


def test_kill_switch_env_enabled(monkeypatch):
    """测试环境变量启用"""
    monkeypatch.delenv("STOCK_HUB_EXECUTION_DISABLED", raising=False)
    # 需要确保文件开关也不存在
    assert KillSwitch.check() is False


def test_kill_switch_file_exists(tmp_path, monkeypatch):
    """测试文件开关存在"""
    # 清除环境变量
    monkeypatch.delenv("STOCK_HUB_EXECUTION_DISABLED", raising=False)

    # 创建 STOP_TRADING 文件
    stop_file = Path.home() / '.stock-hub' / 'STOP_TRADING'
    stop_file.parent.mkdir(parents=True, exist_ok=True)
    stop_file.touch()

    try:
        assert KillSwitch.check() is True
    finally:
        stop_file.unlink()
