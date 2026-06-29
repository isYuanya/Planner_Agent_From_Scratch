"""
orchestration 包 —— 核心编排层 (Core Orchestration Layer)
==========================================================

本包是 Agent 的"大脑"，负责将用户问题转化为可执行计划、校验计划、
调度工具执行、并生成最终答案。所有 AI 决策逻辑集中于此。

模块说明:
---------
- agent.py             : Agent 类 —— 总调度器
- planner.py           : Planner 类 —— 调用 DeepSeek LLM 生成 JSON 计划
- validator.py         : Validator 类 —— 校验工具名 & {step_id} 依赖
- answer_generator.py  : AnswerGenerator 类 —— 根据 trace 生成最终答案


╔══════════════════════════════════════════════════════════════════════════╗
║                  编排层完整数据流 (Agent.run 主循环)                      ║
╚══════════════════════════════════════════════════════════════════════════╝

    entry 层
       │
       │  question: str = "DPO哪年提出？再算一下2023+2024等于几"
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Agent.run(question)                                                  │
│                                                                       │
│  ① self.messages.append({                      ← 追加用户消息到记忆   │
│         "role": "user",                                               │
│         "content": question                                           │
│     })                                                                │
│                                                                       │
│  ② recent_messages = self.messages[-6:]        ← 取最近6条作为上下文  │
│                                                                       │
│     self.messages 格式 (多轮对话记忆):                                  │
│     [                                                                 │
│         {"role": "user", "content": "DPO哪年提出？"},                  │
│         {"role": "assistant", "content": "DPO于2023年提出..."},        │
│         {"role": "user", "content": "那作者是谁？"}                    │
│     ]                                                                 │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ③ Planner.create_plan(question, recent_messages)                     │
│                                                                       │
│     Planner 内部流程:                                                  │
│                                                                       │
│     build_prompt()                                                    │
│       ├── get_system_prompt()    ← 工具描述 + 规则 + JSON 示例         │
│       └── format_messages()      ← 历史对话 → 纯文本                   │
│              │                                                        │
│              ▼                                                        │
│     call_llm(prompt)                                                  │
│       └── DeepSeek API (model="deepseek-chat", temperature=0.1)       │
│              │                                                        │
│              ▼                                                        │
│     parse_plan(content)                                               │
│       └── re.search(r"\[.*\]", content, re.DOTALL) → json.loads()     │
│              │                                                        │
│              ▼                                                        │
│     plan: list = [                     ← Planner 输出的 JSON Plan     │
│         {                                                             │
│             "id":   "step1",            ← 步骤唯一标识                 │
│             "tool": "rag",             ← 工具名 (必须在 TOOLS 中)      │
│             "input": "DPO哪年提出"      ← 工具输入 (可含 {step_id})    │
│         },                                                            │
│         {                                                             │
│             "id":   "step2",                                           │
│             "tool": "calculator",                                     │
│             "input": "2023+{step1}"     ← {step1} 引用上一步输出       │
│         }                                                             │
│     ]                                                                 │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ④ Validator.validate(plan)    ← 最多重试 3 次                        │
│                                                                       │
│     校验规则:                                                          │
│     ├── ① step["tool"] in TOOLS ?     ← 工具名合法性                  │
│     │      └── 否 → {"success": False, "error": "未知工具: xxx"}      │
│     └── ② {变量} 指向有效 step_id ?    ← 依赖合法性                   │
│            └── 否 → {"success": False, "error": "未知依赖: xxx"}      │
│                                                                       │
│     成功返回:  {"success": True}                                       │
│                                                                       │
│     失败时 → Planner.replan(question, old_plan, error, messages)       │
│              └── LLM 根据错误信息重新生成 Plan                          │
│              └── 最多 3 次, 全失败返回 "规划失败"                       │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ 校验通过
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⑤ ToolExecutor.execute(plan)    ← 详见 core 包文档                  │
│                                                                       │
│     execution_result = {                                              │
│         "results": {                   ← 结果字典, key=step_id        │
│             "step1": "DPO（Direct Preference Optimization）"           │
│                      "由Rafael Rafailov等人于2023年提出...",           │
│             "step2": "4047"                                           │
│         },                                                            │
│         "trace": [                     ← 完整执行轨迹                 │
│             {                                                         │
│                 "step_id": "step1",                                    │
│                 "tool":    "rag",                                      │
│                 "input":   "DPO哪年提出",                              │
│                 "output":  "DPO...于2023年提出...",                    │
│                 "success": True,                                      │
│                 "error":   None                                       │
│             },                                                        │
│             {                                                         │
│                 "step_id": "step2",                                    │
│                 "tool":    "calculator",                               │
│                 "input":   "2023+2024",   ← {step1} 已被解析为 2023   │
│                 "output":  "4047",                                     │
│                 "success": True,                                      │
│                 "error":   None                                       │
│             }                                                         │
│         ]                                                             │
│     }                                                                 │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ 取出 trace
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⑥ self.execution_logs.append({        ← 内存临时缓存 (运行历史)      │
│         "question": "DPO哪年提出？再算一下2023+2024...",              │
│         "plan":     [上面步骤列表],                                    │
│         "trace":    [上面 trace 列表]                                  │
│     })                                                                │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⑦ AnswerGenerator.generate_answer(question, trace)                   │
│                                                                       │
│     build_prompt()  →  将 trace 格式化为文本:                          │
│         "步骤 step1：                                                  │
│            使用工具：rag                                               │
│            输入内容：DPO哪年提出                                        │
│            执行结果：DPO...于2023年提出..."                              │
│                                                                       │
│     DeepSeek API (model="deepseek-chat", temperature=0.1)             │
│                                                                       │
│     answer: str = "DPO（Direct Preference Optimization）"              │
│                    "于2023年由Rafael Rafailov等人提出。"                │
│                    "2023+2024的计算结果是4047。"                        │
└──────────────────┬───────────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ⑧ LogRepository.save(question, plan, trace, answer)                  │
│     └── 持久化到 SQLite (详见 persistence 包)                          │
│                                                                       │
│  ⑨ self.messages.append({                     ← 追加助手回复到记忆    │
│         "role": "assistant",                                          │
│         "content": answer                                             │
│     })                                                                │
│                                                                       │
│  ⑩ return answer                                                     │
└──────────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════╗
║                     模块间调用关系 (方框图)                               ║
╚══════════════════════════════════════════════════════════════════════════╝

    ┌────────────────────────────────────────────────────────────┐
    │                      agent.py (Agent)                      │
    │                                                            │
    │  核心属性:                                                  │
    │  ├── self.planner: Planner              ← LLM 计划生成     │
    │  ├── self.validator: Validator          ← 计划校验         │
    │  ├── self.answer_generator: AnswerGenerator ← 答案生成    │
    │  ├── self.tool_registry: ToolRegistry    ← 工具注册表      │
    │  ├── self.tool_executor: ToolExecutor    ← 工具执行器      │
    │  ├── self.log_repository: LogRepository  ← 数据持久化      │
    │  ├── self.messages: list[dict]           ← 多轮对话记忆    │
    │  ├── self.execution_logs: list[dict]     ← 运行历史快照    │
    │  └── self.max_attempts: int = 3          ← 最大重试次数    │
    │                                                            │
    └──┬──────┬──────┬──────┬──────┬──────┬─────────────────────┘
       │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼
    ┌────┐┌────┐┌────┐┌────┐┌────┐┌──────────────────┐
    │Plan││Vali││Answ││Tool││Tool││  LogRepository   │
    │ner ││dator││erGen││Reg ││Exec││  (persistence)  │
    └──┬─┘└──┬─┘└────┘└────┘└──┬─┘└────────┬─────────┘
       │     │                 │            │
       │     │  from tools     │  from core │  from persistence
       │     │  import TOOLS   │            │
       │     ▼                 ▼            ▼
       │  ┌──────────┐   ┌──────────┐  ┌──────────┐
       │  │ tools/   │   │ core/    │  │persistence│
       │  │ __init__ │   │tool_reg  │  │/log_repo  │
       │  │ .TOOLS   │   │tool_exec │  │/db.py     │
       │  └──────────┘   │var_resolv│  └──────────┘
       │                 └──────────┘
       │
       ▼
   from infrastructure
      .logger import logger

对外依赖:
    - core/          : ToolRegistry, ToolExecutor, VariableResolver
    - tools/         : TOOLS 字典 (rag, calculator, weather, db)
    - persistence/   : LogRepository
    - infrastructure/: logger
"""