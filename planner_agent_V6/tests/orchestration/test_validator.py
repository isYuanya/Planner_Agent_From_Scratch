"""
tests/orchestration/test_validator.py

测试 Validator —— 工具合法性校验, 变量依赖校验, 边界情况。
"""

import pytest
from orchestration.validator import Validator
from core.tool_registry import ToolRegistry
from tools import TOOLS


@pytest.fixture
def validator():
    """创建 Validator 实例, 注入与 Agent 相同的 ToolRegistry"""
    registry = ToolRegistry()
    for name, func in TOOLS.items():
        registry.register(name, func)
    return Validator(registry)


class TestValidPlans:
    """合法计划"""

    def test_single_step_valid(self, validator):
        plan = [{"id": "step1", "tool": "calculator", "input": "1+1"}]
        assert validator.validate(plan)["success"] is True

    def test_multi_step_with_variable(self, validator):
        plan = [
            {"id": "step1", "tool": "rag", "input": "DPO"},
            {"id": "step2", "tool": "calculator", "input": "{step1}+1"},
        ]
        assert validator.validate(plan)["success"] is True

    def test_all_registered_tools(self, validator):
        """所有 4 个注册工具都应该通过"""
        for tool_name in ["rag", "calculator", "weather", "db"]:
            plan = [{"id": "s1", "tool": tool_name, "input": "test"}]
            result = validator.validate(plan)
            assert result["success"] is True, f"工具 {tool_name} 应该合法"

    def test_empty_plan(self, validator):
        """空计划也应视为合法 (无步骤可执行)"""
        assert validator.validate([])["success"] is True


class TestUnknownTool:
    """未知工具检测"""

    def test_unknown_tool(self, validator):
        plan = [{"id": "step1", "tool": "nonexistent", "input": "hello"}]
        result = validator.validate(plan)
        assert result["success"] is False
        assert "未知工具" in result["error"]

    def test_unknown_tool_case_sensitive(self, validator):
        """工具名大小写敏感, RAG ≠ rag"""
        plan = [{"id": "step1", "tool": "RAG", "input": "test"}]
        result = validator.validate(plan)
        assert result["success"] is False
        assert "未知工具" in result["error"]

    def test_second_step_unknown_tool(self, validator):
        """多步计划中第二个工具不合法"""
        plan = [
            {"id": "s1", "tool": "calculator", "input": "1+1"},
            {"id": "s2", "tool": "ghost", "input": "x"},
        ]
        result = validator.validate(plan)
        assert result["success"] is False


class TestDependencyCheck:
    """变量依赖校验"""

    def test_valid_dependency(self, validator):
        plan = [
            {"id": "s1", "tool": "calculator", "input": "1+1"},
            {"id": "s2", "tool": "weather", "input": "{s1}"},
        ]
        assert validator.validate(plan)["success"] is True

    def test_unknown_dependency(self, validator):
        plan = [
            {"id": "s1", "tool": "calculator", "input": "{nonexistent}"},
        ]
        result = validator.validate(plan)
        assert result["success"] is False
        assert "未知依赖" in result["error"]

    def test_self_reference_passes_validation(self, validator):
        """步骤引用自己技术上通过校验 (s1 在 step_ids 中),
        但执行时 VariableResolver 无法解析自己的输出 (因为尚未执行)。
        这是 Validator 的已知局限 —— 它不检查执行顺序, 只检查 ID 是否存在。"""
        plan = [
            {"id": "s1", "tool": "calculator", "input": "{s1}+1"},
        ]
        result = validator.validate(plan)
        assert result["success"] is True  # s1 存在于 step_ids

    def test_backward_reference_valid(self, validator):
        """后步引用前步 — 合法"""
        plan = [
            {"id": "s1", "tool": "rag", "input": "DPO"},
            {"id": "s2", "tool": "calculator", "input": "{s1}"},
        ]
        assert validator.validate(plan)["success"] is True

    def test_forward_reference_passes_validation(self, validator):
        """前步引用后步 — Validator 只检查 s2 是否在 step_ids 中,
        不检查执行顺序。这是已知局限, 实际错误会在 ToolExecutor 中暴露。"""
        plan = [
            {"id": "s1", "tool": "calculator", "input": "{s2}"},
            {"id": "s2", "tool": "rag", "input": "DPO"},
        ]
        result = validator.validate(plan)
        assert result["success"] is True  # s2 存在于 step_ids 中

    def test_no_braces_passthrough(self, validator):
        """不含 {} 的输入不触发依赖检查"""
        plan = [{"id": "s1", "tool": "rag", "input": "plain text"}]
        assert validator.validate(plan)["success"] is True