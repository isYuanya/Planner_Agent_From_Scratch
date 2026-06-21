import re

TOOLS = {
    "calculator": lambda x: eval(x),
    "rag": lambda x: "2023"
}

plan = [
    {
        "id": "step1",
        "tool": "rag",
        "input": "DPO哪年提出"
    },
    {
        "id": "step2",
        "tool": "calculator",
        "input": "2026-{step1}"
    }
]


class Executor:

    def __init__(self):
        self.state = {}

    def resolve_variable(self, text):

        variables = re.findall(
            r"\{(.*?)\}",
            text
        )

        for var in variables:

            value = self.state[var]

            text = text.replace(
                "{" + var + "}",
                str(value)
            )

        return text

    def execute(self, plan):

        for step in plan:

            tool_name = step["tool"]

            tool_input = self.resolve_variable(
                step["input"]
            )

            result = TOOLS[tool_name](tool_input)

            self.state[step["id"]] = result

        return self.state


executor = Executor()

state = executor.execute(plan)

print(state)