from click import prompt
import re
import json
from logger import logger

class Planner:
    def __init__(self, client):
        self.client = client

    def format_messages(self, messages):

        history = []

        for msg in messages:
            history.append(
                f"{msg['role']}: {msg['content']}"
            )

        return "\n".join(history)

    def get_system_prompt(self):

        return f"""
        你是一个任务规划器。

        可用工具：

        1. rag
        用途：
        知识检索

        2. calculator
        用途：
        数学计算
        
        3. weather
        用途：
        天气查询
        
        规则：

        1. 不允许假设工具执行结果

        2. 如果后续步骤依赖前一步结果

        必须使用变量引用

        格式：

        {{step_id}}

        示例：

        用户：
        DPO哪年提出？
        距离2026几年？

        输出：

        [
          {{
            "id":"step1",
            "tool":"rag",
            "input":"DPO哪年提出"
          }},
          {{
            "id":"step2",
            "tool":"calculator",
            "input":"2026-{{step1}}"
          }}
        ]
        输出格式：

        [
            {{
                "id":"step1",
                "tool":"",
                "input":""
            }}
        ]
        """

    def build_prompt(
            self,
            question,
            messages
    ):
        system_prompt = self.get_system_prompt()

        history_text = self.format_messages(
            messages
        )

        prompt = f"""
        {system_prompt}

        历史对话：

        {history_text}
        
        当前问题：
        
        {question}
        """
        return prompt

    def build_replan_prompt(
            self,
            question,
            old_plan,
            error,
            messages
    ):

        system_prompt = self.get_system_prompt()

        history_text = self.format_messages(
            messages
        )

        import json

        old_plan_text = json.dumps(
            old_plan,
            ensure_ascii=False,
            indent=2
        )

        return f"""
        {system_prompt}

        历史对话：

        {history_text}
        
        当前问题：

        {question}

        上一次计划：

        {old_plan_text}

        错误：

        {error}

        请重新规划
        """

    def parse_plan(self, content):
        try:

            match = re.search(
                r"\[.*\]",
                content,
                re.DOTALL
            )

            if not match:
                return None

            json_text = match.group()

            return json.loads(json_text)

        except Exception as e:

            print("计划解析失败:", e)

            return None



    def call_llm(self, prompt):

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content

        logger.info(
            f"LLM Output:\n{content}"
        )

        return self.parse_plan(content)

    def create_plan(
            self,
            question,
            messages
    ):
        # 拼接完整规划提示词
        prompt = self.build_prompt(
            question,
            messages
        )

        return self.call_llm(prompt)

    def replan(
            self,
            question,
            old_plan,
            error,
            messages
    ):
        prompt = self.build_replan_prompt(
            question,
            old_plan,
            error,
            messages
        )
        return self.call_llm(prompt)
