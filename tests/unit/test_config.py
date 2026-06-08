"""配置管理测试"""

import pytest
from pathlib import Path
from src.config import Settings, load_yaml_config


def test_settings_default():
    """测试默认配置"""
    settings = Settings()
    assert settings.app_name == "Stock Hub"
    assert settings.app_version == "0.1.0"
    # debug 从环境变量读取，默认为 False
    assert isinstance(settings.debug, bool)


def test_settings_from_env(monkeypatch):
    """测试从环境变量加载配置"""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings()
    assert settings.app_name == "Test App"
    assert settings.debug is True


def test_load_yaml_config(tmp_path):
    """测试加载 YAML 配置"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
app_name: Test App
debug: true
data_dir: /tmp/data
""")

    config = load_yaml_config(config_file)
    assert config["app_name"] == "Test App"
    assert config["debug"] is True
    assert config["data_dir"] == "/tmp/data"


def test_load_yaml_config_not_found():
    """测试加载不存在的 YAML 配置"""
    with pytest.raises(FileNotFoundError):
        load_yaml_config(Path("/nonexistent/config.yaml"))
