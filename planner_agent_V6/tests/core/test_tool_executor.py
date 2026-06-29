"""
tests/core/test_tool_executor.py

测试 ToolExecutor —— 遍历 Plan, 解析变量, 调用工具, 重试, 生成 trace。
"""

import pytest
from core.tool_executor import ToolExecutor
from core.tool_registry import ToolRegistry


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register("echo", lambda x: x)
    r.register("double", lambda x: str(int(x) * 2))
    return r


@pytest.fixture
def executor(registry):
    return ToolExecutor(registry)


class TestBasicExecution:
    """基础执行流程"""

    def test_single_step(self, executor):
        plan = [{"id": "s1", "tool": "echo", "input": "hello"}]
        result = executor.execute(plan)
        assert result["results"]["s1"] == "hello"
        assert result["trace"][0]["success"] is True

    def test_multi_step(self, executor):
        plan = [
            {"id": "s1", "tool": "echo", "input": "10"},
            {"id": "s2", "tool": "double", "input": "{s1}"},
        ]
        result = executor.execute(plan)
        assert result["results"]["s1"] == "10"
        assert result["results"]["s2"] == "20"

    def test_trace_structure(self, executor):
        """验证 trace 条目含全部必需字段"""
        plan = [{"id": "s1", "tool": "echo", "input": "test"}]
        result = executor.execute(plan)
        trace = result["trace"][0]
        assert trace["step_id"] == "s1"
        assert trace["tool"] == "echo"
        assert trace["input"] == "test"
        assert trace["output"] == "test"
        assert trace["success"] is True
        assert trace["error"] is None


class TestVariableResolution:
    """变量解析 (通过 ToolExecutor 间接测试 VariableResolver)"""

    def test_variable_from_previous_step(self, executor):
        plan = [
            {"id": "s1", "tool": "echo", "input": "42"},
            {"id": "s2", "tool": "echo", "input": "答案是{s1}"},
        ]
        result = executor.execute(plan)
        assert result["results"]["s2"] == "答案是42"

    def test_missing_variable_raises_exception(self, executor):
        """变量解析失败直接抛出异常 (VariableResolver 在 try/except 外)"""
        plan = [
            {"id": "s1", "tool": "echo", "input": "{nonexistent}"},
        ]
        with pytest.raises(Exception, match="变量引用不存在"):
            executor.execute(plan)


class TestRetryMechanism:
    """重试机制 (MAX_RETRY = 3)"""

    def test_retry_then_succeed(self, executor, registry):
        """前两次失败, 第三次成功"""
        call_count = [0]

        def flaky_tool(x):
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("临时错误")
            return "ok"

        registry.register("flaky", flaky_tool)
        plan = [{"id": "s1", "tool": "flaky", "input": "x"}]
        result = executor.execute(plan)
        assert result["results"]["s1"] == "ok"
        assert result["trace"][0]["success"] is True
        assert call_count[0] == 3

    def test_all_retries_exhausted(self, executor, registry):
        """全部重试失败"""
        def always_fail(x):
            raise RuntimeError("永远失败")

        registry.register("fail", always_fail)
        plan = [{"id": "s1", "tool": "fail", "input": "x"}]
        result = executor.execute(plan)
        assert result["trace"][0]["success"] is False
        assert "永远失败" in result["trace"][0]["error"]
        assert "s1" not in result["results"]


class TestToolNotFound:
    """工具未注册"""

    def test_unregistered_tool_raises(self, executor):
        plan = [{"id": "s1", "tool": "ghost", "input": "x"}]
        with pytest.raises(Exception, match="Tool not found: ghost"):
            executor.execute(plan)


class TestEmptyPlan:
    """空计划"""

    def test_empty_plan(self, executor):
        result = executor.execute([])
        assert result["results"] == {}
        assert result["trace"] == []