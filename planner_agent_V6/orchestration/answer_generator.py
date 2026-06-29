from config import LLM_MODEL


# ── 工具描述 (供 AnswerGenerator 回答"系统能力"类元问题) ──
TOOL_DESCRIPTIONS = {
    "rag":         "知识库检索 —— 查询本地 FAISS 向量知识库中的文档内容",
    "calculator":  "安全计算器 —— AST 白名单安全解析，支持加减乘除、百分比、年份计算",
    "weather":     "天气查询 —— 查询指定城市的天气信息",
    "db":          "历史查询 —— 查询 agent.db 中过往的执行记录 (问题/计划/轨迹/答案)",
    "web_search":  "网络搜索 —— 通过 Tavily API 搜索互联网实时信息",
}


class AnswerGenerator:

    def __init__(self, client):
        self.client = client

    def build_prompt(self, question, trace, tool_names=None):
        """
        构建生成答案的提示词，包含：
        - 系统能力描述 (可用的工具列表)
        - 用户问题
        - 各步骤执行结果 (含成功/失败状态)
        """

        # ── 系统能力 (供回答"你有什么工具"等元问题) ──
        if tool_names:
            tools_desc = "\n".join([
                f"  - {name}: {TOOL_DESCRIPTIONS.get(name, '未知')}"
                for name in tool_names
            ])
            system_info = f"""
当前系统已接入以下工具 ({len(tool_names)} 个):
{tools_desc}
"""
        else:
            system_info = ""

        # ── 格式化 trace ──
        trace_lines = []
        for step in trace:
            status_mark = "✓ 成功" if step["success"] else "✗ 失败"
            output_str = str(step["output"])[:500] if step["output"] is not None else "(无输出)"

            lines = [
                f"步骤 {step['step_id']} [{status_mark}]：",
                f"  使用工具：{step['tool']}",
                f"  输入内容：{step['input']}",
                f"  执行结果：{output_str}",
            ]

            # 失败时附上错误原因
            if not step["success"] and step.get("error"):
                lines.append(f"  失败原因：{step['error']}")

            trace_lines.append("\n".join(lines))

        state_str = "\n\n".join(trace_lines) if trace_lines else "(无执行步骤)"

        prompt = f"""
你是一个专业的答案生成助手，请根据用户问题和执行步骤的结果，生成清晰、准确、简洁的最终答案。
{system_info}
用户问题：{question}

执行步骤及结果：
{state_str}

要求：
1. 优先基于提供的执行结果回答问题
2. 如果用户询问系统能力、可用工具等关于系统本身的问题，请直接根据上述"当前系统已接入以下工具"信息回答
3. 如果所有执行步骤都失败了，请如实告知用户失败原因，不要编造结果
4. 答案要直接回应问题的所有部分
5. 语言简洁明了，避免冗余
"""
        return prompt

    def generate_answer(self, question, trace, tool_names=None):
        """
        生成最终答案：构建提示词 → 调用大模型 → 返回答案
        """
        prompt = self.build_prompt(question, trace, tool_names)

        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        answer = response.choices[0].message.content.strip()
        return answer
