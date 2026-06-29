import json

from infrastructure.logger import logger
from orchestration.planner import Planner
from orchestration.validator import Validator
from orchestration.answer_generator import AnswerGenerator
from core.tool_registry import ToolRegistry
from core.tool_executor import ToolExecutor
from persistence.log_repository import LogRepository
from tools import TOOLS

class Agent:

    def __init__(self, client):

        self.planner = Planner(client)

        self.answer_generator = AnswerGenerator(client)

        self.messages = []

        self.execution_logs = []

        self.max_attempts = 3

        self.tool_registry = ToolRegistry()

        self._register_tools()

        self.validator = Validator(self.tool_registry)

        self.tool_executor = ToolExecutor(
            self.tool_registry
        )

        self.log_repository = LogRepository()

    def _register_tools(self):
        """从 tools/__init__.py 的 TOOLS 字典统一注册,
        新增工具只需在 tools/__init__.py 中添加, 无需修改此处。"""
        for name, func in TOOLS.items():
            self.tool_registry.register(name, func)

    def run(self, question):

        # ──────────────────────────────────────────────
        #  Round Start
        # ──────────────────────────────────────────────
        round_num = len(self.execution_logs) + 1
        logger.info("=" * 56)
        logger.info(f"  Round #{round_num}")
        logger.info(f"  Question : {question}")
        logger.info("=" * 56)

        # 对话历史 (不含当前问题, 避免重复)
        history = self.messages[-6:]

        # ── 对话上下文 ──
        if history:
            logger.debug("  History (recent):")
            for m in history:
                role = m["role"]
                preview = m["content"][:80].replace("\n", " ")
                logger.debug(f"    [{role}] {preview}")

        # ── Plan ──
        plan = self.planner.create_plan(question, history)

        # 当前问题加入对话历史 (plan 生成后)
        self.messages.append({"role": "user", "content": question})

        if plan is None:
            logger.error("  Plan: 生成失败")
            return "规划失败：无法生成有效的执行计划"

        logger.info("  Plan:")
        for step in plan:
            logger.info(f"    {step['id']}: {step['tool']}(\"{step['input']}\")")

        # ── Validate + Replan ──
        attempt = 0
        success = False

        while attempt < self.max_attempts:

            result = self.validator.validate(plan)

            if result["success"]:
                success = True
                break

            logger.warning(f"  Validate 失败 (attempt {attempt+1}): {result['error']}")

            plan = self.planner.replan(
                question,
                plan,
                result["error"],
                history
            )

            if plan is None:
                logger.error("  Replan: 生成失败")
                return "规划失败：重规划未能生成有效计划"

            logger.info("  Replan 结果:")
            for step in plan:
                logger.info(f"    {step['id']}: {step['tool']}(\"{step['input']}\")")

            attempt += 1

        if not success:
            logger.error("  Plan: 校验全部失败")
            return "规划失败"

        # ── Execute ──
        execution_result = self.tool_executor.execute(plan)
        trace = execution_result["trace"]

        # ── Trace ──
        logger.info("  Trace:")
        for t in trace:
            status = "✓" if t["success"] else "✗"
            out_preview = str(t["output"])[:100].replace("\n", "\\n") if t["output"] else "None"
            logger.info(f"    {status} {t['step_id']} | {t['tool']} | → {out_preview}")

        self.execution_logs.append(
            {
                "question": question,
                "plan": plan,
                "trace": trace
            }
        )

        # ── Answer ──
        answer = self.answer_generator.generate_answer(
            question, trace, tool_names=self.tool_registry.list_tools()
        )
        logger.info(f"  Answer  : {answer}")
        logger.info("=" * 56)

        self.log_repository.save(question, plan, trace, answer)

        self.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer