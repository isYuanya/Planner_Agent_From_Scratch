"""
tests/orchestration/test_planner.py

测试 Planner —— parse_plan, format_messages, build_prompt, create_plan。
"""

import pytest
from unittest.mock import Mock
from orchestration.planner import Planner


@pytest.fixture
def planner(mock_client):
    return Planner(mock_client)


class TestParsePlan:
    """JSON Plan 解析"""

    def test_valid_json_plan(self, planner):
        content = '一些前缀 [{"id":"step1","tool":"rag","input":"test"}] 后缀'
        plan = planner.parse_plan(content)
        assert plan == [{"id": "step1", "tool": "rag", "input": "test"}]

    def test_multi_step_json(self, planner):
        content = '[{"id":"s1","tool":"rag","input":"a"},{"id":"s2","tool":"calculator","input":"b"}]'
        plan = planner.parse_plan(content)
        assert len(plan) == 2

    def test_no_brackets_returns_none(self, planner):
        assert planner.parse_plan("没有方括号的内容") is None

    def test_malformed_json_returns_none(self, planner):
        assert planner.parse_plan("[{invalid json]]") is None

    def test_nested_brackets(self, planner):
        """嵌套 [] 时取最外层"""
        content = '[{"id":"s1","tool":"rag","input":"[nested]"}]'
        plan = planner.parse_plan(content)
        assert plan == [{"id": "s1", "tool": "rag", "input": "[nested]"}]

    def test_inline_json(self, planner):
        """LLM 输出常包含 markdown 标记"""
        content = '''```json
        [{"id":"s1","tool":"rag","input":"DPO"}]
        ```'''
        plan = planner.parse_plan(content)
        assert plan == [{"id": "s1", "tool": "rag", "input": "DPO"}]


class TestFormatMessages:
    """对话历史格式化"""

    def test_empty_messages(self, planner):
        assert planner.format_messages([]) == ""

    def test_single_message(self, planner):
        msgs = [{"role": "user", "content": "hello"}]
        result = planner.format_messages(msgs)
        assert result == "user: hello"

    def test_multiple_messages(self, planner):
        msgs = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]
        result = planner.format_messages(msgs)
        assert "user: q1" in result
        assert "assistant: a1" in result
        assert "user: q2" in result


class TestBuildPrompt:
    """提示词构建"""

    def test_build_prompt_contains_question(self, planner):
        prompt = planner.build_prompt("测试问题", [])
        assert "测试问题" in prompt
        assert "任务规划器" in prompt or "rag" in prompt.lower()

    def test_build_prompt_contains_history(self, planner):
        msgs = [{"role": "user", "content": "之前的问题"}]
        prompt = planner.build_prompt("新问题", msgs)
        assert "之前的问题" in prompt


class TestCreatePlan:
    """端到端 Plan 创建 (Mock LLM)"""

    def test_create_plan_calls_llm(self, planner, mock_client):
        plan = planner.create_plan("1+1=?", [])
        assert isinstance(plan, list)
        mock_client.chat.completions.create.assert_called_once()

    def test_create_plan_returns_parsed_json(self, planner, mock_client):
        # mock_client 默认返回 [{"id":"step1","tool":"calculator","input":"1+1"}]
        plan = planner.create_plan("1+1=?", [])
        assert len(plan) == 1
        assert plan[0]["tool"] == "calculator"

    def test_replan_calls_llm_with_error(self, planner, mock_client):
        old_plan = [{"id": "s1", "tool": "bad", "input": "x"}]
        plan = planner.replan(
            "test",
            old_plan,
            "未知工具: bad",
            [],
        )
        assert isinstance(plan, list)
        # 验证 LLM 被调用 (replan prompt 包含错误信息)
        call_args = mock_client.chat.completions.create.call_args
        prompt_text = str(call_args)
        assert "未知工具" in prompt_text or "bad" in prompt_text