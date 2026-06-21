from openai import OpenAI
from agent import Agent
client = OpenAI(
    api_key="sk-1b1323f1c8d343aeaedf1d6ab2f81baa",
    base_url="https://api.deepseek.com"
)

agent = Agent(client)

while True:

    question = input("用户：")

    answer = agent.run(question)

    print("AI:", answer)
