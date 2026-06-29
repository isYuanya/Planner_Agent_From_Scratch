"""
tests/tools/test_weather_tool.py

测试天气查询工具 —— 模拟桩, 验证输出格式。
"""

from tools.weather_tool import weather_tool


class TestWeatherTool:
    """天气查询 (模拟桩)"""

    def test_returns_formatted_string(self):
        result = weather_tool("北京")
        assert "北京" in result
        assert "天气晴朗" in result
        assert "30℃" in result

    def test_different_city(self):
        result = weather_tool("上海")
        assert "上海" in result

    def test_english_city(self):
        result = weather_tool("Tokyo")
        assert "Tokyo" in result
        assert "天气晴朗" in result

    def test_empty_city(self):
        result = weather_tool("")
        assert "天气晴朗 30℃" in result