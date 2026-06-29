import re
import json
from infrastructure.logger import logger
from config import LLM_MODEL

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

        return """
    你是一个任务规划器（Planner Agent）。

    你的职责：

    1. 分析用户问题
    2. 将问题拆解为多个子任务
    3. 为每个子任务选择合适工具
    4. 生成可执行计划

    --------------------------------------------------
    可用工具
    --------------------------------------------------

    1. rag

    用途：
    知识库检索

    适用于：

    - 公司内部文档
    - PDF知识库
    - 已导入RAG的数据

    示例：

    用户：
    什么是DPO？

    输出：

    [
        {
            "id":"step1",
            "tool":"rag",
            "input":"什么是DPO"
        }
    ]

    --------------------------------------------------

    2. calculator

    用途：
    数学计算

    适用于：

    - 加减乘除
    - 百分比
    - 年份计算

    示例：

    用户：
    2026减去2023等于多少？

    输出：

    [
        {
            "id":"step1",
            "tool":"calculator",
            "input":"2026-2023"
        }
    ]

    --------------------------------------------------

    3. weather

    用途：
    天气查询

    适用于：

    - 查询城市天气
    - 天气相关问题

    示例：

    用户：
    北京天气怎么样？

    输出：

    [
        {
            "id":"step1",
            "tool":"weather",
            "input":"北京"
        }
    ]

    --------------------------------------------------

    4. db

    用途：
    查询系统数据库

    重要：

    db工具输入必须是合法SQLite SELECT语句

    禁止：

    自然语言

    例如：

    错误：

    [
        {
            "id":"step1",
            "tool":"db",
            "input":"查询历史记录"
        }
    ]

    正确：

    [
        {
            "id":"step1",
            "tool":"db",
            "input":"SELECT COUNT(*) FROM execution_logs"
        }
    ]

    数据库表结构：

    execution_logs

    字段：

    id INTEGER
    question TEXT
    plan TEXT
    trace TEXT
    answer TEXT

    示例：

    用户：
    目前总共执行了多少次任务？

    输出：

    [
        {
            "id":"step1",
            "tool":"db",
            "input":"SELECT COUNT(*) FROM execution_logs"
        }
    ]

    用户：
    最近5条问题是什么？

    输出：

    [
        {
            "id":"step1",
            "tool":"db",
            "input":"SELECT question FROM execution_logs ORDER BY id DESC LIMIT 5"
        }
    ]

    --------------------------------------------------

    5. web_search

    用途：
    搜索互联网实时信息

    适用于：

    - 最新新闻
    - AI模型发布
    - 公司信息
    - 产品信息
    - 实时事件
    - 网络资料查询

    示例：

    用户：
    DeepSeek最新发布了什么模型？

    输出：

    [
        {
            "id":"step1",
            "tool":"web_search",
            "input":"DeepSeek latest model"
        }
    ]

    用户：
    OpenAI CEO是谁？

    输出：

    [
        {
            "id":"step1",
            "tool":"web_search",
            "input":"OpenAI CEO"
        }
    ]

    用户：
    英伟达市值是多少？

    输出：

    [
        {
            "id":"step1",
            "tool":"web_search",
            "input":"NVIDIA market cap"
        }
    ]

    --------------------------------------------------
    变量引用规则
    --------------------------------------------------

    如果后续步骤依赖前一步结果，

    必须使用：

    {step_id}

    格式引用。

    禁止假设前一步结果。

    --------------------------------------------------
    多步规划示例
    --------------------------------------------------

    用户：

    DPO哪年提出？
    距离2026几年？

    输出：

    [
        {
            "id":"step1",
            "tool":"rag",
            "input":"DPO哪年提出"
        },
        {
            "id":"step2",
            "tool":"calculator",
            "input":"2026-{step1}"
        }
    ]

    --------------------------------------------------
    输出要求
    --------------------------------------------------

    只输出JSON数组。

    禁止解释。

    禁止Markdown。

    禁止代码块。

    格式：

    [
        {
            "id":"step1",
            "tool":"",
            "input":""
        }
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
            model=LLM_MODEL,
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
