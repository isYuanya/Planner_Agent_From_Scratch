# variable_resolver.py

import re


class VariableResolver:

    def resolve(self, text, results):

        if not isinstance(text, str):
            return text

        pattern = r"\{(.*?)\}"

        matches = re.findall(pattern, text)

        for step_id in matches:

            if step_id not in results:
                raise Exception(
                    f"变量引用不存在: {step_id}"
                )

            value = str(results[step_id])

            text = text.replace(
                f"{{{step_id}}}",
                value
            )

        return text