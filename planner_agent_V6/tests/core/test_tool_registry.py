"""
tests/core/test_tool_registry.py

测试 ToolRegistry —— 工具注册、查找、列表。
"""

import pytest
from core.tool_registry import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


def dummy_tool(x):
    return f"dummy: {x}"


class TestRegisterAndGet:
    """注册与查找"""

    def test_register_and_get(self, registry):
        registry.register("dummy", dummy_tool)
        func = registry.get("dummy")
        assert func is dummy_tool
        assert func("hello") == "dummy: hello"

    def test_get_nonexistent(self, registry):
        assert registry.get("nonexistent") is None

    def test_register_multiple(self, registry):
        registry.register("a", lambda x: x)
        registry.register("b", lambda x: x * 2)
        assert registry.get("a") is not None
        assert registry.get("b") is not None

    def test_overwrite_tool(self, registry):
        """同名工具后注册覆盖先注册"""
        registry.register("x", lambda x: "v1")
        registry.register("x", lambda x: "v2")
        assert registry.get("x")("test") == "v2"


class TestListTools:
    """列出已注册工具"""

    def test_empty_registry(self, registry):
        assert registry.list_tools() == []

    def test_list_after_register(self, registry):
        registry.register("rag", dummy_tool)
        registry.register("calc", dummy_tool)
        tools = registry.list_tools()
        assert sorted(tools) == ["calc", "rag"]

    def test_list_reflects_overwrite(self, registry):
        """覆盖注册不会重复"""
        registry.register("x", dummy_tool)
        registry.register("x", dummy_tool)
        assert registry.list_tools() == ["x"]