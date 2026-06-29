from openai import OpenAI
from agent import Agent
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

agent = Agent(client)

while True:

    question = input("用户：")

    answer = agent.run(question)

    print("AI:", answer)
