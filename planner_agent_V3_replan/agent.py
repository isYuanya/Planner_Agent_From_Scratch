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

        self.max_attempts=3

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

        attempt = 0

        success = False

        while attempt < self.max_attempts:

            result = self.validator.validate(plan)

            if result["success"]:
                success = True
                break

            plan = self.planner.replan(
                question,
                plan,
                result["error"],
                recent_messages
            )

            attempt += 1

        if not success:
            return "规划失败"

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
