import re
from tools import TOOLS


class Validator:
    def validate(self, plan):

        step_ids = {
            step["id"]
            for step in plan
        }

        for step in plan:

            # 检查工具

            if step["tool"] not in TOOLS:
                raise Exception(
                    f"未知工具: {step['tool']}"
                )

            # 检查依赖

            variables = re.findall(
                r"\{(.*?)}",
                step["input"]
            )

            for var in variables:

                if var not in step_ids:

                    raise Exception(
                        f"未知依赖: {var}"
                    )

        return True
