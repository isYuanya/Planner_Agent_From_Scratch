import re


class Validator:
    """计划校验器 —— 检查工具合法性 & 变量依赖完整性"""

    def __init__(self, tool_registry):
        """
        Args:
            tool_registry: ToolRegistry 实例,
                           Validator 通过 registry.has() 校验工具名,
                           不再直接依赖 tools/__init__.py 的 TOOLS 字典。
        """
        self.registry = tool_registry

    def validate(self, plan):

        step_ids = {
            step["id"]
            for step in plan
        }

        for step in plan:

            # 检查工具 (通过 ToolRegistry, 与 Agent 共用同一注册表)
            if not self.registry.has(step["tool"]):
                return {
                    "success": False,
                    "error": f"未知工具: {step['tool']}"
                }

            # 检查依赖
            variables = re.findall(
                r"\{(.*?)}",
                step["input"]
            )

            for var in variables:

                if var not in step_ids:
                    return {
                        "success": False,
                        "error": f"未知依赖: {var}"
                    }

        return {
            "success": True
        }
