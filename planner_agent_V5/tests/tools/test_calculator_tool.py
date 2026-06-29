"""
tests/tools/test_calculator_tool.py

测试安全计算器 —— AST 白名单, 防注入, 边界情况。
"""

import pytest
from tools.calculator_tool import calculator_tool, SafeCalculator


@pytest.fixture
def calc():
    return SafeCalculator()


class TestBasicArithmetic:
    """四则运算"""

    def test_addition(self):
        assert calculator_tool("2+3") == 5

    def test_subtraction(self):
        assert calculator_tool("10-7") == 3

    def test_multiplication(self):
        assert calculator_tool("4*5") == 20

    def test_division(self):
        assert calculator_tool("8/2") == 4.0

    def test_compound(self):
        assert calculator_tool("(1+2)*3") == 9

    def test_large_numbers(self):
        assert calculator_tool("999999+1") == 1000000


class TestSecurity:
    """安全防护 —— 阻止代码注入"""

    def test_no_import(self):
        """__import__ 被 AST 白名单阻止"""
        with pytest.raises((ValueError, SyntaxError)):
            calculator_tool("__import__('os').system('ls')")

    def test_no_function_call(self):
        with pytest.raises((ValueError, SyntaxError)):
            calculator_tool("eval('1+1')")

    def test_no_attribute_access(self):
        with pytest.raises((ValueError, SyntaxError)):
            calculator_tool("[].__class__")

    def test_only_arithmetic_allowed(self):
        """仅允许加减乘除和常量, 其他 AST 节点抛出 ValueError"""
        # 取反操作符 (UnaryOp) 不在白名单内
        with pytest.raises((ValueError, SyntaxError)):
            calculator_tool("-5")


class TestEdgeCases:
    """边界情况"""

    def test_zero_division(self, calc):
        with pytest.raises(ZeroDivisionError):
            calc.calculate("1/0")

    def test_empty_expression(self, calc):
        with pytest.raises((ValueError, SyntaxError)):
            calc.calculate("")

    def test_negative_via_subtract(self):
        """用减法实现负数: 0-5 = -5"""
        assert calculator_tool("0-5") == -5