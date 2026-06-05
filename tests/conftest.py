"""测试配置"""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_data_dir(tmp_path):
    """临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_config_dir(tmp_path):
    """临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir
