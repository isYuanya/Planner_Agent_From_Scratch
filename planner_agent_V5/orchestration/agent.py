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

        self.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        recent_messages = self.messages[-6:]

        plan = self.planner.create_plan(
            question,
            recent_messages
        )

        attempt = 0

        success = False

        while attempt < self.max_attempts:

            result = self.validator.validate(
                plan
            )

            if result["success"]:

                success = True

                break

            plan = self.planner.replan(
                question,
                plan,
                result["error"],
                recent_messages
            )

            attempt += 1

        if not success:
            return "规划失败"

        # execution_result —— 工具执行器的完整返回包
        # execution_result = {
        #     # 结果字典：用步骤ID当key，快速取出对应工具的纯输出，变量替换时直接查
        #     "results": {
        #         "step1": "DPO（Direct Preference Optimization）由Rafael Rafailov等人于2023年提出...",
        #         "step2": "4047"
        #     },
        #     # 完整轨迹：就是上面的 trace 列表，用来生成答案、记录存档
        #     "trace": [
        #         {"step_id": "step1", "tool": "rag", "input": "DPO哪年提出", "output": "..."},
        #         {"step_id": "step2", "tool": "calculator", "input": "2023+2024", "output": "4047"}
        #     ]
        # }
        execution_result = (
            self.tool_executor.execute(plan)
        )

        trace = execution_result["trace"]

        # agent.py 里的列表变量，内存临时缓存
        # self.execution_logs = [
        #     # 第一次请求的执行快照
        #     {
        #         "question": "DPO哪年提出？再算一下2023+2024等于几",
        #         "plan": {"steps": [{"id": "step1", "tool": "rag", "input": "DPO哪年提出"}, ...]},
        #         "trace": [上面的 trace 完整列表]
        #     },
        #     # 第二次请求的执行快照
        #     {
        #         "question": "那它的作者是谁？",
        #         "plan": {"steps": [{"id": "step1", "tool": "rag", "input": "DPO的作者"}]},
        #         "trace": [...]
        #     }
        # ]
        self.execution_logs.append(
            {
                "question": question,
                "plan": plan,
                "trace": trace
            }
        )

        answer = (
            self.answer_generator.generate_answer(
                question,
                trace
            )
        )

        # agent.db 里的 execution_logs 表 —— 硬盘永久存档
        self.log_repository.save(
            question,
            plan,
            trace,
            answer
        )


        # self.messages —— 大模型的对话记忆（多轮上下文）
        # self.messages = [
        #     # 系统提示词：给大模型定行为规则，每次调用都会带上
        #     {"role": "system", "content": "你是规划式智能助手，先拆解步骤调用工具，再根据结果回答问题。"},
        #     # 第一轮用户提问
        #     {"role": "user", "content": "DPO哪年提出？再算一下2023+2024等于几"},
        #     # 第一轮AI的最终回答
        #     {"role": "assistant", "content": "DPO于2023年提出，2023+2024的计算结果是4047。"},
        #     # 第二轮用户追问（多轮对话时会持续追加）
        #     {"role": "user", "content": "那它的作者是谁？"}
        # ]
        self.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer