# tool_registry.py

class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name: str, func):
        """
        注册工具
        """
        self.tools[name] = func

    def get(self, name: str):
        """
        获取工具
        """
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.keys())