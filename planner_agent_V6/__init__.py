"""
planner_agent_V5 —— 规划式 AI Agent 项目
=========================================

基于 DeepSeek LLM 的规划式智能代理：将用户问题拆解为执行计划，
调用注册工具逐步执行，并根据执行轨迹生成最终答案。

技术栈: DeepSeek API (OpenAI 兼容) + FastAPI + Streamlit + SQLite + FAISS


╔══════════════════════════════════════════════════════════════════════════════╗
║                        项目六层逻辑架构                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝


  ┌──────────────────────────────────────────────────────────┐
  │                    1. 入口层 (Entry)                       │
  │   main.py (CLI)  │  api.py (FastAPI)  │  app.py (UI)     │
  │                                                          │
  │   职责: 接收用户输入, 创建 Agent 实例, 返回结果              │
  │   启动: python entry/main.py | uvicorn entry.api:app      │
  │         streamlit run entry/app.py                        │
  └────────────────────────┬─────────────────────────────────┘
                           │
                           │ 实例化 Agent(client)
                           │ 调用 Agent.run(question)
                           ▼
  ┌──────────────────────────────────────────────────────────┐
  │               2. 核心编排层 (Orchestration)                │
  │   agent.py ─── 总调度器，串联所有组件                       │
  │   planner.py ── LLM 生成执行计划 (JSON Plan)              │
  │   validator.py ─ 校验计划合理性 (工具 + 依赖)             │
  │   answer_generator.py ─ LLM 生成最终答案                  │
  │                                                          │
  │   职责: AI 决策大脑 — 计划→校验→执行→回答                    │
  │   核心循环: 最多 3 次 replan, 校验失败则重新让 LLM 规划      │
  └────────┬───────────────────────────────────┬─────────────┘
           │                                   │
           │ 调度工具基础设施                    │ 校验工具合法性
           ▼                                   ▼
  ┌────────────────────────┐    ┌─────────────────────────────┐
  │ 3. 工具基础设施层 (core/) │    │  4. 工具实现层 (tools/)      │
  │                         │    │                             │
  │ tool_registry.py       │    │  calculator_tool.py          │
  │   ── {name → func}     │    │   ── AST 安全计算器          │
  │                         │    │                             │
  │ tool_executor.py       │◄───│  weather_tool.py             │
  │   ── 遍历Plan执行工具    │    │   ── 天气查询 (模拟桩)       │
  │   ── 变量解析 + 重试     │    │                             │
  │                         │    │  rag_tool.py                 │
  │ variable_resolver.py   │    │   ── FAISS + Sentence        │
  │   ── {step_id} 替换     │    │      Transformer 知识检索   │
  │                         │    │                             │
  │   职责: 工具调度引擎      │    │  db_tool.py                 │
  │   连接 Plan ↔ Tool      │    │   ── 查询历史执行记录        │
  └────────┬───────────────┘    │                             │
           │                    │  汇总: tools/__init__.py     │
           │                    │  TOOLS = {rag, calculator,   │
           │                    │    weather, db}              │
           │                    │                             │
           │                    │  职责: 具体工具实现           │
           │                    │  供 Agent 调用,              │
           │                    │  供 Validator 校验           │
           │                    └──────────┬──────────────────┘
           │                               │
           │  工具执行结果持久化              │ db_tool 查询历史
           ▼                               ▼
  ┌──────────────────────────────────────────────────────────┐
  │               5. 数据持久层 (Persistence)                   │
  │                                                          │
  │   log_repository.py ── CRUD 操作 (仓库模式)               │
  │     ├── save(question, plan, trace, answer)              │
  │     └── execute_query(sql) → list[tuple]                 │
  │                                                          │
  │   db.py ── SQLite 连接 + 建表                             │
  │     └── execution_logs(id, question, plan, trace, answer) │
  │                                                          │
  │   agent.db ── 运行时数据库文件                             │
  │                                                          │
  │   职责: 每次运行的 (问题, 计划, 轨迹, 答案) 持久化存档       │
  └──────────────────────────────────────────────────────────┘
           ▲
           │ 全局日志
           │
  ┌────────┴─────────────────────────────────────────────────┐
  │               6. 基础设施层 (Infrastructure)               │
  │                                                          │
  │   logger.py ── 全局日志配置                               │
  │     ├── 输出: logs/agent.log (UTF-8)                      │
  │     ├── 输出: sys.stdout (控制台)                          │
  │     └── 格式: 时间 | 级别 | 消息                           │
  │                                                          │
  │   legacy_tools.py ── 已废弃的旧工具 (孤立文件 ⚠)           │
  │                                                          │
  │   职责: 跨模块共享的基础组件 (不包含业务逻辑)                │
  └──────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                        完整执行流程 (一次用户请求)                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

   用户输入: "DPO哪年提出？再算一下2023+2024等于几"
   │
   ▼
   entry 层 ──► Agent.run(question)
   │
   ▼
   Planner.create_plan()
     └──► DeepSeek LLM 生成:
          [
            {"id":"step1","tool":"rag","input":"DPO哪年提出"},
            {"id":"step2","tool":"calculator","input":"2023+{step1}"}
          ]
   │
   ▼
   Validator.validate(plan)
     ├── 检查 "rag" in TOOLS ?        → ✅
     ├── 检查 "calculator" in TOOLS ? → ✅
     ├── 检查 {step1} 指向有效步骤?    → ✅
     └── 失败时 → Planner.replan() (最多3次)
   │
   ▼
   ToolExecutor.execute(plan)
     ├── step1: VariableResolver → ToolRegistry.get("rag") → rag_tool("DPO哪年提出")
     │         └──► "DPO由Rafael Rafailov等人于2023年提出..."
     └── step2: VariableResolver 将 {step1}→"2023" → ToolRegistry.get("calculator")
               └──► calculator_tool("2023+2024") → "4047"
     返回:
     {
       "results": {"step1": "DPO...于2023年提出...", "step2": "4047"},
       "trace": [
         {"step_id":"step1","tool":"rag","input":"DPO哪年提出",
          "output":"DPO...于2023年提出...","success":true,"error":null},
         {"step_id":"step2","tool":"calculator","input":"2023+2024",
          "output":"4047","success":true,"error":null}
       ]
     }
   │
   ▼
   AnswerGenerator.generate_answer(question, trace)
     └──► DeepSeek LLM 根据 trace 生成:
          "DPO于2023年由Rafael Rafailov等人提出，2023+2024=4047。"
   │
   ▼
   LogRepository.save(question, plan, trace, answer)
     └──► INSERT INTO execution_logs → agent.db
   │
   ▼
   返回 answer 给用户


╔══════════════════════════════════════════════════════════════════════════════╗
║                    跨包依赖关系总览                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

    entry ──────────► orchestration ──────────► core
      │                    │                      │
      │                    ├──────────────────────┤
      │                    │                      │
      │                    ▼                      ▼
      │              tools ◄──────────── infrastructure
      │                │
      │                ├──► persistence
      │                │
      └────────────────┴── (无直接依赖)

    依赖规则:
    - entry      → orchestration (创建 Agent)
    - orchestration → core + tools + persistence + infrastructure (编排所有组件)
    - core       → infrastructure (日志)
    - tools      → persistence (db_tool 查询历史)
    - persistence → (无项目内依赖, 仅标准库 sqlite3)
    - infrastructure → (无项目内依赖, 仅标准库 logging)


╔══════════════════════════════════════════════════════════════════════════════╗
║                    运行时启动方式                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

    # CLI 交互式对话
    python -m entry.main

    # FastAPI 服务 (供 Streamlit / 外部调用)
    uvicorn entry.api:app --host 0.0.0.0 --port 8000

    # Streamlit 聊天界面
    streamlit run entry/app.py

    # Docker 部署
    docker build -t planner-agent .
    docker run -p 8000:8000 --env-file .env planner-agent
"""