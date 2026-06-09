"""代理基类测试"""

import pytest
from src.plugins.agents.base import AnalysisAgent


class MockAgent(AnalysisAgent):
    @property
    def system_prompt(self) -> str:
        return "你是一位测试代理。"


@pytest.fixture
def mock_agent():
    return MockAgent(ai_adapter=None, plugins=[])


def test_agent_system_prompt(mock_agent):
    assert "测试代理" in mock_agent.system_prompt


def test_agent_initialization(mock_agent):
    assert mock_agent.ai_adapter is None
    assert mock_agent.plugins == []
