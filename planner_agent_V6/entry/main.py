from openai import OpenAI
from orchestration.agent import Agent
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

agent = Agent(client)

while True:

    question = input("用户：")

    answer = agent.run(question)

    print("AI:", answer)
