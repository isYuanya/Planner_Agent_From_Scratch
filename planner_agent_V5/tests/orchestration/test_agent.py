"""
tests/orchestration/test_agent.py

测试 Agent 总调度器 —— 完整 run() 流程, 重规划, 失败路径。
"""

import pytest
from unittest.mock import Mock, call
from orchestration.agent import Agent


@pytest.fixture
def agent():
    return Agent(client=None)


@pytest.fixture
def mocked_agent(agent):
    """替换所有内部组件为 Mock 的 Agent"""
    agent.planner = Mock()
    agent.validator = Mock()
    agent.tool_executor = Mock()
    agent.answer_generator = Mock()
    agent.log_repository = Mock()
    return agent


class TestBasicRun:
    """正常流程: plan → validate → execute → answer"""

    def test_successful_run(self, mocked_agent):
        mocked_agent.planner.create_plan.return_value = [
            {"id": "step1", "tool": "calculator", "input": "1+1"},
        ]
        mocked_agent.validator.validate.return_value = {"success": True}
        mocked_agent.tool_executor.execute.return_value = {
            "results": {"step1": "2"},
            "trace": [
                {"step_id": "step1", "tool": "calculator",
                 "input": "1+1", "output": "2", "success": True, "error": None},
            ],
        }
        mocked_agent.answer_generator.generate_answer.return_value = "答案是2"

        answer = mocked_agent.run("1+1=?")

        assert answer == "答案是2"
        mocked_agent.planner.create_plan.assert_called_once()
        mocked_agent.validator.validate.assert_called_once()
        mocked_agent.tool_executor.execute.assert_called_once()
        mocked_agent.answer_generator.generate_answer.assert_called_once()
        mocked_agent.log_repository.save.assert_called_once()

    def test_messages_appended(self, mocked_agent):
        """验证 user 和 assistant 消息被正确追加到 messages"""
        mocked_agent.planner.create_plan.return_value = [
            {"id": "s1", "tool": "calculator", "input": "1+1"},
        ]
        mocked_agent.validator.validate.return_value = {"success": True}
        mocked_agent.tool_executor.execute.return_value = {
            "results": {"s1": "2"}, "trace": [],
        }
        mocked_agent.answer_generator.generate_answer.return_value = "2"

        assert len(mocked_agent.messages) == 0
        mocked_agent.run("q1")
        assert len(mocked_agent.messages) == 2
        assert mocked_agent.messages[0] == {"role": "user", "content": "q1"}
        assert mocked_agent.messages[1] == {"role": "assistant", "content": "2"}

    def test_execution_logs_appended(self, mocked_agent):
        """验证运行历史被记录到 execution_logs"""
        plan = [{"id": "s1", "tool": "calculator", "input": "1+1"}]
        trace = [{"step_id": "s1", "tool": "calculator", "input": "1+1",
                   "output": "2", "success": True, "error": None}]

        mocked_agent.planner.create_plan.return_value = plan
        mocked_agent.validator.validate.return_value = {"success": True}
        mocked_agent.tool_executor.execute.return_value = {
            "results": {"s1": "2"}, "trace": trace,
        }
        mocked_agent.answer_generator.generate_answer.return_value = "2"

        assert len(mocked_agent.execution_logs) == 0
        mocked_agent.run("1+1=?")
        assert len(mocked_agent.execution_logs) == 1
        log = mocked_agent.execution_logs[0]
        assert log["question"] == "1+1=?"
        assert log["plan"] == plan
        assert log["trace"] == trace


class TestReplanFlow:
    """重规划流程 (校验失败 → replan)"""

    def test_replan_on_first_validation_failure(self, mocked_agent):
        """第一次校验失败, replan 后通过"""
        plan_v1 = [{"id": "s1", "tool": "unknown_tool", "input": "x"}]
        plan_v2 = [{"id": "s1", "tool": "calculator", "input": "1+1"}]

        mocked_agent.planner.create_plan.return_value = plan_v1
        mocked_agent.planner.replan.return_value = plan_v2
        # validator: 第一次失败, 第二次成功
        mocked_agent.validator.validate.side_effect = [
            {"success": False, "error": "未知工具: unknown_tool"},
            {"success": True},
        ]
        mocked_agent.tool_executor.execute.return_value = {
            "results": {"s1": "2"}, "trace": [],
        }
        mocked_agent.answer_generator.generate_answer.return_value = "ok"

        answer = mocked_agent.run("test")
        assert answer == "ok"
        assert mocked_agent.planner.replan.call_count == 1
        assert mocked_agent.validator.validate.call_count == 2

    def test_max_retries_exhausted(self, mocked_agent):
        """3次全部校验失败, 返回 '规划失败'"""
        mocked_agent.planner.create_plan.return_value = [
            {"id": "s1", "tool": "bad", "input": "x"},
        ]
        mocked_agent.planner.replan.return_value = [
            {"id": "s1", "tool": "bad", "input": "x"},
        ]
        mocked_agent.validator.validate.return_value = {
            "success": False, "error": "未知工具: bad",
        }

        answer = mocked_agent.run("test")
        assert answer == "规划失败"
        # max_attempts=3: attempt=0(validate→replan), 1(validate→replan), 2(validate→replan)
        # 每次失败都触发 replan, 共 3 次
        assert mocked_agent.validator.validate.call_count == 3
        assert mocked_agent.planner.replan.call_count == 3
        # 失败后不应执行
        mocked_agent.tool_executor.execute.assert_not_called()
        mocked_agent.answer_generator.generate_answer.assert_not_called()