"""
entry 包 —— 入口层 (Entry Layer)
================================

本包包含应用的所有启动入口，负责接收用户输入并创建 Agent 实例。

模块说明:
---------
- main.py : CLI 命令行入口 —— 交互式终端对话循环
- api.py  : FastAPI 服务入口 —— 提供 POST /chat 接口供前端/外部调用
- app.py  : Streamlit 前端入口 —— 浏览器聊天界面

启动方式:
---------
    CLI:        python -m entry.main           (或 python entry/main.py)
    API 服务:    uvicorn entry.api:app --port 8000
    Streamlit:  streamlit run entry/app.py


╔══════════════════════════════════════════════════════════════════════════╗
║                         入口层架构与数据流                                ║
╚══════════════════════════════════════════════════════════════════════════╝

                        ┌──────────────────────┐
                        │     👤 最终用户       │
                        └──────┬───────┬───────┘
                               │       │
              ┌────────────────┘       └────────────────┐
              ▼                                         ▼
   ┌─────────────────────┐                 ┌─────────────────────┐
   │   main.py (CLI)     │                 │  app.py (Streamlit) │
   │                     │                 │                     │
   │  input("用户：")     │                 │  st.chat_input()    │
   │  → str (question)   │                 │  → str (question)   │
   └──────────┬──────────┘                 └──────────┬──────────┘
              │                                       │
              │  agent.run(question)                  │  POST /chat
              │                                       │  Body: {"query": question}
              │                                       ▼
              │                           ┌─────────────────────┐
              │                           │   api.py (FastAPI)  │
              │                           │                     │
              │                           │  ChatRequest:       │
              │                           │  { "query": str }    │
              │                           │                     │
              │                           │  Response:           │
              │                           │  { "answer": str }   │
              │                           └──────────┬──────────┘
              │                                       │
              │                           agent.run(request.query)
              │                                       │
              ▼                                       ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │                                                                 │
   │              client = OpenAI(                                    │
   │                  api_key = os.getenv("DEEPSEEK_API_KEY"),        │
   │                  base_url = "https://api.deepseek.com"           │
   │              )                                                   │
   │                                                                 │
   │              agent = Agent(client)   ◄── 导入自 orchestration    │
   │                                                                 │
   │              answer = agent.run(question)                        │
   │                         │                                        │
   │                         ▼                                        │
   │                   "DPO于2023年提出，2023+2024=4047"   ← str      │
   │                                                                 │
   └─────────────────────────────────────────────────────────────────┘

三个入口的数据格式:

    ┌──────────────┬─────────────────────┬──────────────────────┐
    │   入口       │   输入格式           │   输出格式            │
    ├──────────────┼─────────────────────┼──────────────────────┤
    │ main.py      │ input() → str       │ print(answer) → str  │
    │ api.py       │ {"query": str}      │ {"answer": str}      │
    │ app.py       │ st.chat_input → str │ st.write(answer)     │
    └──────────────┴─────────────────────┴──────────────────────┘

跨包依赖:
    entry/*.py
      └── orchestration.agent.Agent   (核心调度器)
      └── openai.OpenAI               (DeepSeek API 客户端)
      └── dotenv.load_dotenv          (加载 .env 环境变量)
"""