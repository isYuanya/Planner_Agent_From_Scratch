import re
from tools import TOOLS


class Executor:

    @staticmethod
    def resolve_variable(text, state):
        """
        将:
        2026-{step1}

        替换为:

        2026-2023
        """

        variables = re.findall(
            r"\{(.*?)}",
            text
        )

        for var in variables:

            value = state[var]["result"]

            text = text.replace(
                "{" + var + "}",
                str(value)
            )

        return text

    def execute(self, plan):

        # 当前任务自己的运行状态
        state = {}

        for step in plan:

            tool_name = step["tool"]

            # 变量替换
            tool_input = self.resolve_variable(
                step["input"],
                state
            )

            # 调用工具
            result = TOOLS[tool_name](
                tool_input
            )

            # 保存执行结果
            state[step["id"]] = {
                "tool": tool_name,
                "input": tool_input,
                "result": result
            }

        return state