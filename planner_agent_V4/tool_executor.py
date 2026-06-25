from variable_resolver import VariableResolver
from logger import logger

class ToolExecutor:

    MAX_RETRY = 3

    def __init__(
            self,
            tool_registry
    ):

        self.registry = tool_registry

        self.trace = []

        self.resolver = VariableResolver()

    def execute(
            self,
            plan
    ):

        results = {}

        self.trace = []

        for step in plan:

            step_id = step["id"]

            tool_name = step["tool"]

            logger.info(
                f"Execute Tool: {tool_name}"
            )

            raw_input = step["input"]

            # 变量解析
            tool_input = self.resolver.resolve(
                raw_input,
                results
            )

            tool = self.registry.get(
                tool_name
            )

            if tool is None:

                raise Exception(
                    f"Tool not found: {tool_name}"
                )

            success = False

            output = None

            error = None

            # Retry机制
            for retry in range(
                    self.MAX_RETRY
            ):

                try:

                    output = tool(
                        tool_input
                    )

                    success = True

                    logger.info(
                        f"Tool Success: {tool_name}"
                    )

                    break

                except Exception as e:

                    error = str(e)

                    if retry == (
                        self.MAX_RETRY - 1
                    ):
                        success = False


            # 保存结果
            if success:

                results[step_id] = output
            else:
                logger.error(
                    f"Tool Failed: {tool_name} | {error}"
                )

            # Trace
            self.trace.append(
                {
                    "step_id": step_id,
                    "tool": tool_name,
                    "input": tool_input,
                    "output": output,
                    "success": success,
                    "error": error
                }
            )

        return {
            "results": results,
            "trace": self.trace
        }