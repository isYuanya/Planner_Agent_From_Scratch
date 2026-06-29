import re
import json
from infrastructure.logger import logger
from config import LLM_MODEL
from jsonschema import validate, ValidationError
from .schema import PLAN_SCHEMA


class Planner:
    MAX_PLAN_STEPS = 20

    def __init__(self, client):
        self.client = client

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

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"rag",
                    "input":"什么是DPO"
                }
            ]
        }

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

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"calculator",
                    "input":"2026-2023"
                }
            ]
        }

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

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"weather",
                    "input":"北京"
                }
            ]
        }

        --------------------------------------------------

        4. db

        用途：

        查询系统数据库

        重要：

        db工具输入必须是合法SQLite SELECT语句。

        禁止输入自然语言。

        例如：

        错误：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"db",
                    "input":"查询历史记录"
                }
            ]
        }

        正确：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"db",
                    "input":"SELECT COUNT(*) FROM execution_logs"
                }
            ]
        }

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

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"db",
                    "input":"SELECT COUNT(*) FROM execution_logs"
                }
            ]
        }

        用户：
        最近5条问题是什么？

        输出：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"db",
                    "input":"SELECT question FROM execution_logs ORDER BY id DESC LIMIT 5"
                }
            ]
        }

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

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"web_search",
                    "input":"DeepSeek latest model"
                }
            ]
        }

        用户：
        OpenAI CEO是谁？

        输出：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"web_search",
                    "input":"OpenAI CEO"
                }
            ]
        }

        用户：
        英伟达市值是多少？

        输出：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"web_search",
                    "input":"NVIDIA market cap"
                }
            ]
        }

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

        {
            "plan":[
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
        }

        --------------------------------------------------
        输出要求
        --------------------------------------------------

        必须输出合法JSON对象。

        不要输出任何解释。

        不要输出Markdown。

        不要输出代码块。

        最外层必须是JSON对象。

        格式必须严格如下：

        {
            "plan":[
                {
                    "id":"step1",
                    "tool":"",
                    "input":""
                }
            ]
        }
        """

    def build_replan_message(
            self,
            question,
            old_plan,
            error
    ):

        old_plan_text = json.dumps(
            old_plan,
            ensure_ascii=False,
            indent=2
        )

        return f"""
        当前问题：
    
        {question}
    
        上一次生成的计划：
    
        {old_plan_text}
    
        Validator返回的错误：
    
        {error}
    
        请修正上述错误。
    
        重新生成新的执行计划。
    
        仍然必须严格按照JSON格式返回：
    
        {{
            "plan":[
                {{
                    "id":"step1",
                    "tool":"",
                    "input":""
                }}
            ]
        }}
        """

    def _validate_plan(self, plan):

        # 1. 不允许空计划
        if not plan:
            raise ValueError(
                "plan不能为空"
            )

        # 2. Step 数量限制
        if len(plan) > self.MAX_PLAN_STEPS:
            raise ValueError(
                "plan步骤过多"
            )

        step_ids = set()

        for step in plan:

            # 3. id 唯一
            if step["id"] in step_ids:
                raise ValueError(
                    f"重复的step id: {step['id']}"
                )

            step_ids.add(
                step["id"]
            )

            # 4. id格式
            if not re.fullmatch(
                    r"step\d+",
                    step["id"]
            ):
                raise ValueError(
                    f"非法step id: {step['id']}"
                )

            # 5. tool不能为空
            if not step["tool"].strip():
                raise ValueError(
                    "tool不能为空"
                )

            # 6. input不能为空
            if not step["input"].strip():
                raise ValueError(
                    "input不能为空"
                )

    # 将LLM返回的JSON字符串解析成Python Plan对象
    def parse_plan(self, content):

        data = None

        # ── 第 1 层: 直接解析 (response_format="json_object" 时 LLM 返回纯 JSON) ──
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            pass

        # ── 第 2 层: 正则兜底 (LLM 有时会在 JSON 外包裹 markdown 或说明文字) ──
        if data is None:
            try:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    data = json.loads(match.group())

            except (json.JSONDecodeError, AttributeError):

                logger.error(f"JSON 正则提取也失败, 原始输出:\n{content}")

                return None

        # ── JSON Schema 校验 ──
        try:
            validate(instance=data, schema=PLAN_SCHEMA)

        except ValidationError as e:

            logger.error(f"JSON Schema校验失败: {e.message}")

            return None

        except Exception:

            # data 可能仍是 None (如果两层解析都跳过了)
            logger.error(f"JSON Schema校验失败: 输入不是有效 JSON 对象")

            return None

        plan = data["plan"]

        # ── Planner 自身业务校验 ──
        try:
            self._validate_plan(plan)
        except Exception as e:
            logger.error(f"Plan业务校验失败: {e}")
            return None

        return plan

    def call_llm(
            self,
            system_prompt,
            history_messages,
            user_message
    ):

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(history_messages)

        messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        # ── 日志：发送给 LLM 的消息摘要 ──
        logger.debug(f"  → LLM request: {len(messages)} messages")
        for i, m in enumerate(messages):
            # system prompt 只显示第一行, user/assistant 截断到 80 字符
            if m["role"] == "system":
                first_line = m["content"].strip().split("\n")[0]
                logger.debug(f"    [{m['role']}] {first_line}")
            else:
                preview = m["content"][:80].replace("\n", " ")
                logger.debug(f"    [{m['role']}] {preview}")

        response = self.client.chat.completions.create(

            model=LLM_MODEL,

            messages=messages,

            temperature=0.1,

            response_format={
                "type": "json_object"
            }

        )

        content = response.choices[0].message.content

        # 精简版 LLM 输出 (json 串一行显示)
        compact = content.replace("\n", " ").replace("  ", " ")
        logger.info(f"  LLM Output: {compact[:200]}")

        return self.parse_plan(content)

    def create_plan(
            self,
            question,
            messages
    ):
        # 拼接完整规划提示词
        system_prompt = self.get_system_prompt()

        return self.call_llm(
            system_prompt,
            messages,
            question
        )

    def replan(
            self,
            question,
            old_plan,
            error,
            messages
    ):

        system_prompt = self.get_system_prompt()

        replan_message = self.build_replan_message(
            question,
            old_plan,
            error
        )

        return self.call_llm(
            system_prompt,
            messages,
            replan_message
        )
