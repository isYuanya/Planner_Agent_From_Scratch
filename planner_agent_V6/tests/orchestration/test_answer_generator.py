"""
tests/orchestration/test_answer_generator.py

测试 AnswerGenerator —— build_prompt, generate_answer。
"""

import pytest
from unittest.mock import Mock
from orchestration.answer_generator import AnswerGenerator


@pytest.fixture
def generator(mock_client):
    return AnswerGenerator(mock_client)


@pytest.fixture
def sample_trace():
    return [
        {
            "step_id": "step1",
            "tool": "rag",
            "input": "DPO哪年提出",
            "output": "DPO由Rafael Rafailov等人于2023年提出",
            "success": True,
            "error": None,
        },
        {
            "step_id": "step2",
            "tool": "calculator",
            "input": "2023+2024",
            "output": "4047",
            "success": True,
            "error": None,
        },
    ]


class TestBuildPrompt:
    """提示词构建"""

    def test_contains_question(self, generator):
        prompt = generator.build_prompt("什么是DPO?", [])
        assert "什么是DPO?" in prompt

    def test_contains_trace_steps(self, generator, sample_trace):
        prompt = generator.build_prompt("test", sample_trace)
        assert "step1" in prompt
        assert "rag" in prompt
        assert "DPO哪年提出" in prompt
        assert "step2" in prompt
        assert "calculator" in prompt

    def test_contains_instruction(self, generator):
        """提示词应包含回答要求"""
        prompt = generator.build_prompt("q", [])
        assert "专业" in prompt or "答案" in prompt

    def test_empty_trace(self, generator):
        prompt = generator.build_prompt("问题", [])
        assert "问题" in prompt
        # 空 trace 不会崩溃
        assert isinstance(prompt, str)


class TestGenerateAnswer:
    """答案生成 (Mock LLM)"""

    def test_generate_answer_returns_string(self, generator, sample_trace):
        answer = generator.generate_answer("DPO哪年提出？", sample_trace)
        # mock_client 默认返回 "[{...}]" 格式, generate_answer 直接返回 .strip()
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_generate_answer_calls_llm(self, generator, sample_trace, mock_client):
        generator.generate_answer("test q", sample_trace)
        mock_client.chat.completions.create.assert_called_once()

    def test_generate_answer_strips_whitespace(self, generator, mock_client):
        """验证返回内容被 strip"""
        response = Mock()
        response.choices = [
            Mock(message=Mock(content="  答案有前后空格  \n"))
        ]
        mock_client.chat.completions.create.return_value = response

        answer = generator.generate_answer("q?", [])
        assert answer == "答案有前后空格"