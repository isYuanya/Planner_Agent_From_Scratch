from planner import Planner
from validator import Validator
from executor import Executor
from answer_generator import AnswerGenerator

class Agent:

    def __init__(self, client):

        self.planner = Planner(client)

        self.validator = Validator()

        self.executor = Executor()

        self.answer_generator = AnswerGenerator(client)

        self.messages = []

    def run(self, question):
        # 1. 保存用户消息

        self.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        # 2. 取最近6条消息

        recent_messages = self.messages[-6:]

        # 3. 规划

        plan = self.planner.create_plan(
            question,
            recent_messages
        )

        # 4. 校验

        if self.validator.validate(plan):
            # 5. 执行

            state = self.executor.execute(plan)

            # 6. 生成答案

            answer = self.answer_generator.generate_answer(
                question,
                state
            )

            # 7. 保存AI回复

            self.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            return answer