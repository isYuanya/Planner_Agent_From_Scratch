from fastapi import FastAPI
from pydantic import BaseModel

from dotenv import load_dotenv
from openai import OpenAI
import os

from agent import Agent

# 读取.env
load_dotenv()

# 创建DeepSeek客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 创建Agent实例
agent = Agent(client)

# 创建FastAPI应用
app = FastAPI()


# 请求格式
class ChatRequest(BaseModel):
    query: str


# 聊天接口
@app.post("/chat")
def chat(request: ChatRequest):

    answer = agent.run(request.query)

    return {
        "answer": answer
    }