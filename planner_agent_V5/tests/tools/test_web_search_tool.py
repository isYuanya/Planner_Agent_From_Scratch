"""
tests/tools/test_web_search_tool.py

测试网页搜索工具 —— Mock TavilyClient, 验证结果格式化。
"""

import pytest
from unittest.mock import Mock, patch


class TestWebSearchTool:
    """web_search_tool 测试 (Mock Tavily)"""

    @pytest.fixture(autouse=True)
    def setup_mock(self):
        """Mock TavilyClient 避免真实 API 调用"""
        self.mock_client = Mock()
        self.mock_client.search.return_value = {
            "results": [
                {"content": "DeepSeek V3 是..."},
                {"content": "DeepSeek R1 推理模型..."},
                {"content": "DeepSeek Coder 支持..."},
            ]
        }

        with patch("tools.web_search_tool.client", self.mock_client):
            yield

    def test_returns_joined_results(self):
        from tools.web_search_tool import web_search_tool
        result = web_search_tool("DeepSeek")
        assert "DeepSeek V3 是..." in result
        assert "DeepSeek R1 推理模型..." in result
        assert "DeepSeek Coder 支持..." in result

    def test_results_separated_by_newline(self):
        from tools.web_search_tool import web_search_tool
        result = web_search_tool("test")
        lines = result.split("\n")
        assert len(lines) == 3

    def test_empty_results(self):
        self.mock_client.search.return_value = {"results": []}
        from tools.web_search_tool import web_search_tool
        result = web_search_tool("noresults")
        assert result == ""

    def test_search_params_passed_correctly(self):
        from tools.web_search_tool import web_search_tool
        web_search_tool("query123")
        self.mock_client.search.assert_called_once_with(
            query="query123",
            search_depth="basic",
            max_results=5,
        )
