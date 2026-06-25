class AnswerGenerator:

    def __init__(self, client):
        self.client = client

    def build_prompt(
            self,
            question,
            trace
    ):
        """
        构建生成答案的提示词，包含用户问题和各步骤执行结果
        """
        # 格式化trace为易读的字符串
        state_str = "\n".join([
            f"步骤 {step['step_id']}：\n"
            f"  使用工具：{step['tool']}\n"
            f"  输入内容：{step['input']}\n"
            f"  执行结果：{step['output']}"
            for step in trace
        ])

        prompt = f"""
        你是一个专业的答案生成助手，请根据用户问题和执行步骤的结果，生成清晰、准确、简洁的最终答案。

        用户问题：{question}

        执行步骤及结果：
        {state_str}

        要求：
        1. 基于提供的执行结果回答问题，不要编造信息
        2. 答案要直接回应问题的所有部分
        3. 语言简洁明了，避免冗余
        """
        return prompt

    def generate_answer(
            self,
            question,
            trace
    ):
        """
        生成最终答案：构建提示词 → 调用大模型 → 返回答案
        """
        # 1. 构建提示词
        prompt = self.build_prompt(question, trace)

        # 2. 调用大模型生成答案
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # 低随机性保证答案准确性
        )

        # 3. 提取并返回答案
        answer = response.choices[0].message.content.strip()
        return answer