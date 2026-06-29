"""
tests/core/test_variable_resolver.py

测试 VariableResolver —— {step_id} 变量替换。
"""

import pytest
from core.variable_resolver import VariableResolver


@pytest.fixture
def resolver():
    return VariableResolver()


class TestBasicResolution:
    """基础变量替换"""

    def test_single_variable(self, resolver):
        result = resolver.resolve(
            "2026-{step1}",
            {"step1": "2023"}
        )
        assert result == "2026-2023"

    def test_multiple_variables(self, resolver):
        result = resolver.resolve(
            "{a} + {b} = ?",
            {"a": "1", "b": "2"}
        )
        assert result == "1 + 2 = ?"

    def test_same_variable_twice(self, resolver):
        result = resolver.resolve(
            "{x} and {x}",
            {"x": "hello"}
        )
        assert result == "hello and hello"

    def test_no_variables(self, resolver):
        result = resolver.resolve(
            "plain text",
            {"step1": "ignored"}
        )
        assert result == "plain text"

    def test_variable_value_is_int(self, resolver):
        """变量值不是字符串时, 自动转 str"""
        result = resolver.resolve(
            "count: {n}",
            {"n": 42}
        )
        assert result == "count: 42"

    def test_non_string_input_passthrough(self, resolver):
        """非字符串输入原样返回"""
        assert resolver.resolve(123, {}) == 123
        assert resolver.resolve(None, {}) is None


class TestEdgeCases:
    """边界情况"""

    def test_missing_variable_raises(self, resolver):
        with pytest.raises(Exception, match="变量引用不存在"):
            resolver.resolve("{unknown}", {"step1": "ok"})

    def test_empty_text(self, resolver):
        assert resolver.resolve("", {}) == ""

    def test_partial_brace_not_replaced(self, resolver):
        """单独的 { 或 } 不被当作变量"""
        result = resolver.resolve("not a {var", {"var": "x"})
        assert result == "not a {var"  # 不匹配 r"\{(.*?)\}"

    def test_variable_with_special_chars(self, resolver):
        """变量名含中文或特殊字符"""
        result = resolver.resolve(
            "结果: {步骤一}",
            {"步骤一": "成功"}
        )
        assert result == "结果: 成功"