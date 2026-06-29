"""
core 包 —— 工具基础设施层 (Tool Infrastructure Layer)
=====================================================

本包提供工具注册、执行和变量解析的底层机制，是连接"计划"与"工具实现"的桥梁。

模块说明:
---------
- tool_registry.py    : ToolRegistry 类 —— 中心化工具注册表
- tool_executor.py    : ToolExecutor 类 —— 执行引擎 (含重试 + 变量解析)
- variable_resolver.py: VariableResolver 类 —— {step_id} 变量替换


╔══════════════════════════════════════════════════════════════════════════╗
║                  core 包内部数据流 (ToolExecutor.execute)                ║
╚══════════════════════════════════════════════════════════════════════════╝

    输入: plan (来自 Planner)
    ─────────────────────────
    plan = [
        {"id": "step1", "tool": "rag",        "input": "DPO哪年提出"},
        {"id": "step2", "tool": "calculator", "input": "2023+{step1}"}
    ]

    ┌─────────────────────────────────────────────────────────────────┐
    │  ToolExecutor.execute(plan)                                     │
    │                                                                  │
    │  MAX_RETRY = 3   ← 每个工具步骤最多重试 3 次                      │
    │                                                                  │
    │  results = {}     ← 累积结果, key=step_id, 供变量解析查询         │
    │  self.trace = []  ← 执行轨迹, 供 AnswerGenerator 生成答案         │
    │                                                                  │
    │  for step in plan:                                               │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │  ① 变量解析: VariableResolver.resolve(raw_input, results) │    │
    │  │                                                            │    │
    │  │  输入: raw_input = "2023+{step1}"                          │    │
    │  │        results    = {"step1": "2023"}                      │    │
    │  │                                                            │    │
    │  │  内部逻辑:                                                  │    │
    │  │    re.findall(r"\{(.*?)\}", text)  →  ["step1"]            │    │
    │  │    text.replace("{step1}", results["step1"])               │    │
    │  │                                                            │    │
    │  │  输出: tool_input = "2023+2024"    ← 已解析的纯字符串       │    │
    │  │                                                            │    │
    │  │  异常: 若 step_id 不存在 → raise Exception("变量引用不存在") │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │  ② 工具查找: ToolRegistry.get(tool_name)                  │    │
    │  │                                                            │    │
    │  │  self.registry.tools = {                                   │    │
    │  │      "rag":        <function rag_tool>,                    │    │
    │  │      "calculator": <function calculator_tool>,             │    │
    │  │      "weather":    <function weather_tool>,                │    │
    │  │      "db":         <function db_tool>                      │    │
    │  │  }                                                         │    │
    │  │                                                            │    │
    │  │  未找到 → raise Exception("Tool not found: xxx")            │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │  ③ 工具调用 (含重试机制, MAX_RETRY=3):                    │    │
    │  │                                                            │    │
    │  │  for retry in range(3):                                    │    │
    │  │      try:                                                  │    │
    │  │          output = tool(tool_input)   ← 调用真实工具函数    │    │
    │  │          success = True                                    │    │
    │  │          break                                             │    │
    │  │      except Exception as e:                                │    │
    │  │          error = str(e)                                    │    │
    │  │          if retry == 2: success = False                    │    │
    │  │                                                            │    │
    │  │  成功: results[step_id] = output                           │    │
    │  │  失败: logger.error("Tool Failed: ...")                    │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │      │                                                           │
    │      ▼                                                           │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │  ④ 记录轨迹: self.trace.append({...})                     │    │
    │  │                                                            │    │
    │  │  trace_entry = {                                           │    │
    │  │      "step_id": "step1",                                    │    │
    │  │      "tool":    "rag",                                      │    │
    │  │      "input":   "DPO哪年提出",                              │    │
    │  │      "output":  "DPO...于2023年提出...",                    │    │
    │  │      "success": True,                                       │    │
    │  │      "error":   None                                        │    │
    │  │  }                                                          │    │
    │  └─────────────────────────────────────────────────────────┘    │
    │                                                                  │
    │  循环结束, 返回:                                                  │
    │  return {                                                        │
    │      "results": {                                                │
    │          "step1": "DPO...于2023年提出...",                       │
    │          "step2": "4047"                                         │
    │      },                                                          │
    │      "trace": [ trace_entry_step1, trace_entry_step2 ]           │
    │  }                                                               │
    └─────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════╗
║                    三大组件关系与职责                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

                        ┌──────────────────────────┐
                        │     ToolExecutor         │
                        │     (执行引擎)            │
                        │                          │
                        │  遍历 plan 中的每个 step  │
                        │  协调 Resolver + Registry │
                        │  管理重试 + 生成 trace    │
                        └───┬──────────┬───────────┘
                            │          │
              ┌─────────────┘          └─────────────┐
              ▼                                      ▼
   ┌──────────────────────┐            ┌──────────────────────┐
   │  VariableResolver    │            │   ToolRegistry       │
   │  (变量解析器)         │            │   (工具注册表)        │
   │                      │            │                      │
   │  resolve(text,       │            │  register(name,func) │
   │          results)    │            │  get(name) → func    │
   │                      │            │  list_tools() → list │
   │  输入: "2023+{step1}"│            │                      │
   │  results:            │            │  self.tools = {      │
   │    {"step1":"2023"}  │            │    "rag": rag_tool,  │
   │                      │            │    "calc": calc_tool,│
   │  输出: "2023+2024"   │            │    ...               │
   │                      │            │  }                   │
   │  re.findall(         │            │                      │
   │    r"\{(.*?)\}",     │            └──────────────────────┘
   │    text              │
   │  ) → ["step1"]       │
   └──────────────────────┘

    数据流方向:
        plan → ToolExecutor → ① VariableResolver.resolve()  (解析 {var})
                            → ② ToolRegistry.get()         (查找函数)
                            → ③ tool(tool_input)            (执行, 最多3次)
                            → ④ trace.append()              (记录轨迹)
                            → return {results, trace}


╔══════════════════════════════════════════════════════════════════════════╗
║                    对外依赖关系                                           ║
╚══════════════════════════════════════════════════════════════════════════╝

    core/tool_executor.py
      ├── core/variable_resolver.py   (相对导入: .variable_resolver)
      └── infrastructure/logger.py    (日志记录)

    core/tool_registry.py
      └── (无外部依赖, 纯内存字典)

    core/variable_resolver.py
      └── re  (标准库)
"""
