"""信号生成器测试"""

import pytest
from datetime import datetime
from src.research.signals.generator import SignalGenerator, Signal, SignalStatus, SignalSource


@pytest.fixture
def signal_generator():
    """信号生成器实例"""
    return SignalGenerator()


def test_create_signal(signal_generator):
    """测试创建信号"""
    targets = {
        "600519.SSE": 0.3,
        "000858.SZE": 0.2,
    }
    signal = signal_generator.create_signal(
        targets=targets,
        source=SignalSource.MANUAL,
    )
    assert signal.schema_version == "v1"
    assert signal.source == SignalSource.MANUAL
    assert signal.status == SignalStatus.DRAFT
    assert signal.targets == targets


def test_validate_signal_valid(signal_generator):
    """测试验证有效信号"""
    targets = {
        "600519.SSE": 0.3,
        "000858.SZE": 0.2,
    }
    signal = signal_generator.create_signal(targets=targets)
    is_valid, issues = signal_generator.validate_signal(signal)
    assert is_valid is True
    assert len(issues) == 0


def test_validate_signal_over_weight(signal_generator):
    """测试验证超重信号"""
    targets = {
        "600519.SSE": 0.6,
        "000858.SZE": 0.6,
    }
    signal = signal_generator.create_signal(targets=targets)
    is_valid, issues = signal_generator.validate_signal(signal)
    assert is_valid is False
    assert any("总权重" in issue for issue in issues)


def test_validate_signal_invalid_symbol(signal_generator):
    """测试验证无效标的"""
    targets = {
        "600519": 0.3,  # 缺少交易所后缀
    }
    signal = signal_generator.create_signal(targets=targets)
    is_valid, issues = signal_generator.validate_signal(signal)
    assert is_valid is False
    assert any("标的格式错误" in issue for issue in issues)


def test_approve_signal(signal_generator):
    """测试审批信号"""
    targets = {"600519.SSE": 0.5}
    signal = signal_generator.create_signal(targets=targets)
    assert signal.status == SignalStatus.DRAFT

    approved = signal_generator.approve_signal(signal)
    assert approved.status == SignalStatus.APPROVED


def test_publish_signal(signal_generator):
    """测试发布信号"""
    targets = {"600519.SSE": 0.5}
    signal = signal_generator.create_signal(targets=targets)
    approved = signal_generator.approve_signal(signal)
    published = signal_generator.publish_signal(approved)
    assert published.status == SignalStatus.PUBLISHED


def test_reject_signal(signal_generator):
    """测试拒绝信号"""
    targets = {"600519.SSE": 0.5}
    signal = signal_generator.create_signal(targets=targets)
    rejected = signal_generator.reject_signal(signal, reason="风控拒绝")
    assert rejected.status == SignalStatus.REJECTED
    assert rejected.metadata["reject_reason"] == "风控拒绝"
