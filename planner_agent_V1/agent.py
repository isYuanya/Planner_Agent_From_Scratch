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
        plan = self.planner.create_plan(question)

        if self.validator.validate(plan):

            state = self.executor.execute(plan)

            return self.answer_generator.generate_answer(question,state)
