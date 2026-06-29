from fastapi import FastAPI
from pydantic import BaseModel
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
)
from openai import OpenAI
from orchestration.agent import Agent


# 创建DeepSeek客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
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