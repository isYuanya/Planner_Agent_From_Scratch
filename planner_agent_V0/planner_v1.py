from openai import OpenAI

client = OpenAI(
    api_key="sk-xxxx",
    base_url="https://api.deepseek.com"
)

class Planner:
    def __init__(self, client):
        self.client = client

    def build_prompt(self, question):
        prompt = f"""
        你是一个任务规划器。

        可用工具：

        1. rag
        用途：
        知识检索

        2. calculator
        用途：
        数学计算
        
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

        用户问题：

        {question}
        """
        return prompt

    def parse_plan(self, content):
        import json

        try:
            plan = json.loads(content)
            return plan

        except Exception as e:
            print("计划解析失败:", e)
            return None

    def create_plan(self, question):
        # 1. 拼接完整规划提示词
        prompt = self.build_prompt(question)

        # 2. 调用大模型生成计划文本
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )

        # 3. 取出模型返回的JSON计划字符串
        content = response.choices[0].message.content

        # 4. 返回原始计划文本（后续交给parse_plan解析）
        return self.parse_plan(content)



# 使用
planner = Planner(client)

plan = planner.create_plan(
    "DPO哪年提出？距离2026相差几年"
)
print(plan)