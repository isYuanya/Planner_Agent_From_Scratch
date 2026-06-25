from planner import Planner
from validator import Validator
from answer_generator import AnswerGenerator
from tools.calculator_tool import calculator_tool
from tool_registry import ToolRegistry
from tool_executor import ToolExecutor
from log_repository import LogRepository

class Agent:

    def __init__(self, client):

        self.planner = Planner(client)

        self.validator = Validator()

        self.answer_generator = AnswerGenerator(client)

        self.messages = []

        self.execution_logs = []

        self.max_attempts = 3

        self.tool_registry = ToolRegistry()

        self.tool_executor = ToolExecutor(
            self.tool_registry
        )

        self._register_tools()

        self.log_repository = LogRepository()

    def _register_tools(self):

        def rag_tool(query):
            return f"[rag result] {query}"

        def weather_tool(city):
            return f"{city}天气晴朗 30℃"

        self.tool_registry.register(
            "rag",
            rag_tool
        )

        self.tool_registry.register(
            "calculator",
            calculator_tool
        )

        self.tool_registry.register(
            "weather",
            weather_tool
        )

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

        execution_result = (
            self.tool_executor.execute(plan)
        )

        state = execution_result["results"]

        trace = execution_result["trace"]

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
                state
            )
        )

        self.log_repository.save(
            question,
            plan,
            trace,
            answer
        )

        self.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        return answer