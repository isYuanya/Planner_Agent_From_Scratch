from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import DEEPSEEK_BASE_URL
from openai import OpenAI
from orchestration.agent import Agent

# ── FastAPI 应用 ──
app = FastAPI(title="Planner Agent", version="6.0")

# ── Agent 延迟初始化, 由 /configure 接口注入 Key 后创建 ──
agent: Agent = None


# ── 请求 / 响应格式 ──
class ChatRequest(BaseModel):
    query: str


class ConfigureRequest(BaseModel):
    deepseek_key: str
    tavily_key: str = ""


class ConfigureResponse(BaseModel):
    status: str
    message: str


@app.get("/health")
def health():
    """Docker HEALTHCHECK + 前端连接状态检测"""
    return {"status": "ok", "configured": agent is not None}


@app.post("/configure")
def configure(request: ConfigureRequest):
    """运行时注入 API Key, 创建 Agent 实例"""
    global agent

    if not request.deepseek_key.strip():
        raise HTTPException(status_code=400, detail="DeepSeek API Key 不能为空")

    client = OpenAI(
        api_key=request.deepseek_key.strip(),
        base_url=DEEPSEEK_BASE_URL,
    )

    # 注入 Tavily Key 到环境变量 (web_search_tool 通过 os.getenv 读取)
    import os
    if request.tavily_key.strip():
        os.environ["TAVILY_API_KEY"] = request.tavily_key.strip()

    agent = Agent(client)

    return ConfigureResponse(
        status="ok",
        message="Agent 已就绪, 可以开始对话"
    )


@app.post("/chat")
def chat(request: ChatRequest):
    """聊天接口 —— 需先 /configure 才能使用"""
    if agent is None:
        raise HTTPException(
            status_code=400,
            detail="请先配置 API Key: POST /configure"
        )

    answer = agent.run(request.query)

    return {"answer": answer}