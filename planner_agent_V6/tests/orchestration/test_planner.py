"""
tests/orchestration/test_planner.py

测试 Planner (V6) —— parse_plan, _validate_plan, build_replan_message,
create_plan, replan。
"""

import pytest
from unittest.mock import Mock
from orchestration.planner import Planner


@pytest.fixture
def planner(mock_client):
    return Planner(mock_client)


# ═══════════════════════════════════════════════════════════════════════════
#  parse_plan
# ═══════════════════════════════════════════════════════════════════════════

class TestParsePlan:
    """JSON Plan 解析 (V6: json.loads + 正则兜底 + JSON Schema)"""

    def test_valid_json_object(self, planner):
        """response_format="json_object" 的标准输出"""
        content = '{"plan":[{"id":"step1","tool":"rag","input":"test"}]}'
        plan = planner.parse_plan(content)
        assert plan == [{"id": "step1", "tool": "rag", "input": "test"}]

    def test_multi_step(self, planner):
        content = '{"plan":[{"id":"step1","tool":"rag","input":"a"},{"id":"step2","tool":"calculator","input":"b"}]}'
        plan = planner.parse_plan(content)
        assert len(plan) == 2

    def test_markdown_code_block(self, planner):
        """正则兜底: LLM 有时仍会包裹 markdown"""
        content = '```json\n{"plan":[{"id":"step1","tool":"rag","input":"DPO"}]}\n```'
        plan = planner.parse_plan(content)
        assert plan == [{"id": "step1", "tool": "rag", "input": "DPO"}]

    def test_extra_text_around_json(self, planner):
        """正则兜底: JSON 前后有说明文字"""
        content = '这是执行计划：\n{"plan":[{"id":"step1","tool":"weather","input":"北京"}]}\n请执行。'
        plan = planner.parse_plan(content)
        assert plan == [{"id": "step1", "tool": "weather", "input": "北京"}]

    def test_no_json_returns_none(self, planner):
        assert planner.parse_plan("没有任何JSON内容") is None

    def test_malformed_json_returns_none(self, planner):
        assert planner.parse_plan("{invalid json]]") is None

    def test_missing_plan_key(self, planner):
        """Schema 要求顶层有 "plan" 字段"""
        content = '{"steps":[{"id":"s1","tool":"rag","input":"x"}]}'
        assert planner.parse_plan(content) is None

    def test_step_missing_required_field(self, planner):
        """Schema required: id, tool, input"""
        content = '{"plan":[{"tool":"rag","input":"x"}]}'
        assert planner.parse_plan(content) is None

    def test_additional_properties_rejected(self, planner):
        """Schema additionalProperties: false"""
        content = '{"plan":[{"id":"s1","tool":"rag","input":"x","extra":"field"}]}'
        assert planner.parse_plan(content) is None


# ═══════════════════════════════════════════════════════════════════════════
#  _validate_plan (业务校验)
# ═══════════════════════════════════════════════════════════════════════════

class TestValidatePlan:
    """Planner 自身业务校验"""

    def test_valid_plan_passes(self, planner):
        plan = [{"id": "step1", "tool": "rag", "input": "test"}]
        planner._validate_plan(plan)  # 不抛异常即通过

    def test_empty_plan_raises(self, planner):
        with pytest.raises(ValueError, match="plan不能为空"):
            planner._validate_plan([])

    def test_duplicate_ids_raises(self, planner):
        plan = [
            {"id": "step1", "tool": "rag", "input": "a"},
            {"id": "step1", "tool": "calculator", "input": "b"},
        ]
        with pytest.raises(ValueError, match="重复的step id"):
            planner._validate_plan(plan)

    def test_invalid_id_format_raises(self, planner):
        plan = [{"id": "s1", "tool": "rag", "input": "x"}]
        with pytest.raises(ValueError, match="非法step id"):
            planner._validate_plan(plan)

    def test_empty_tool_raises(self, planner):
        plan = [{"id": "step1", "tool": "  ", "input": "x"}]
        with pytest.raises(ValueError, match="tool不能为空"):
            planner._validate_plan(plan)

    def test_empty_input_raises(self, planner):
        plan = [{"id": "step1", "tool": "rag", "input": ""}]
        with pytest.raises(ValueError, match="input不能为空"):
            planner._validate_plan(plan)

    def test_too_many_steps_raises(self, planner):
        plan = [
            {"id": f"step{i}", "tool": "rag", "input": "x"}
            for i in range(1, 22)  # MAX_PLAN_STEPS = 20
        ]
        with pytest.raises(ValueError, match="步骤过多"):
            planner._validate_plan(plan)

    def test_numeric_id_valid(self, planner):
        """step1, step2, ... step999 都是合法格式"""
        plan = [
            {"id": "step1", "tool": "rag", "input": "a"},
            {"id": "step999", "tool": "calculator", "input": "b"},
        ]
        planner._validate_plan(plan)  # 不抛异常


# ═══════════════════════════════════════════════════════════════════════════
#  build_replan_message
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildReplanMessage:
    """重规划消息构建"""

    def test_contains_question(self, planner):
        msg = planner.build_replan_message("测试问题", [], "某错误")
        assert "测试问题" in msg

    def test_contains_error(self, planner):
        msg = planner.build_replan_message("q", [], "未知工具: bad")
        assert "未知工具: bad" in msg

    def test_contains_old_plan(self, planner):
        old_plan = [{"id": "step1", "tool": "bad", "input": "x"}]
        msg = planner.build_replan_message("q", old_plan, "err")
        assert "step1" in msg
        assert "bad" in msg


# ═══════════════════════════════════════════════════════════════════════════
#  create_plan / replan (Mock LLM)
# ═══════════════════════════════════════════════════════════════════════════

class TestCreatePlan:
    """端到端 Plan 创建 (Mock LLM)"""

    def test_create_plan_calls_llm(self, planner, mock_client):
        plan = planner.create_plan("1+1=?", [])
        assert isinstance(plan, list)
        mock_client.chat.completions.create.assert_called_once()

    def test_create_plan_returns_parsed_plan(self, planner):
        plan = planner.create_plan("1+1=?", [])
        assert len(plan) == 1
        assert plan[0]["tool"] == "calculator"
        assert plan[0]["input"] == "1+1"

    def test_replan_calls_llm(self, planner, mock_client):
        old_plan = [{"id": "step1", "tool": "bad", "input": "x"}]
        plan = planner.replan("test", old_plan, "未知工具: bad", [])
        assert isinstance(plan, list)
        assert mock_client.chat.completions.create.call_count >= 1

    def test_create_plan_returns_none_on_bad_llm_output(self, planner, mock_client):
        """LLM 返回无法解析的内容 → 返回 None"""
        response = Mock()
        response.choices = [
            Mock(message=Mock(content="这不是JSON"))
        ]
        mock_client.chat.completions.create.return_value = response
        plan = planner.create_plan("test", [])
        assert plan is None


# ═══════════════════════════════════════════════════════════════════════════
#  call_llm (消息组装)
# ═══════════════════════════════════════════════════════════════════════════

class TestCallLLM:
    """call_llm 消息组装"""

    def test_system_prompt_sent_as_system_role(self, planner, mock_client):
        planner.call_llm("sys prompt", [], "user msg")
        call_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert call_messages[0] == {"role": "system", "content": "sys prompt"}

    def test_user_message_at_end(self, planner, mock_client):
        planner.call_llm("sys", [], "user msg")
        call_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert call_messages[-1] == {"role": "user", "content": "user msg"}

    def test_history_inserted_between(self, planner, mock_client):
        history = [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "a1"}]
        planner.call_llm("sys", history, "q2")
        call_messages = mock_client.chat.completions.create.call_args[1]["messages"]
        assert call_messages[0]["role"] == "system"
        assert call_messages[1]["role"] == "user"
        assert call_messages[1]["content"] == "q1"
        assert call_messages[2]["role"] == "assistant"
        assert call_messages[2]["content"] == "a1"
        assert call_messages[3]["role"] == "user"
        assert call_messages[3]["content"] == "q2"

    def test_response_format_is_json_object(self, planner, mock_client):
        planner.call_llm("sys", [], "user msg")
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}