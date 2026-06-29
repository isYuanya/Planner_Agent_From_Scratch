"""
tools 包 —— 工具实现层 (Tool Implementation Layer)
===================================================

本包包含 Agent 可调用的所有具体工具实现，每个工具是一个独立的模块。
所有工具通过本 __init__.py 汇总到 TOOLS 字典中，供 Validator 校验
和 Agent 注册使用。


╔══════════════════════════════════════════════════════════════════════════╗
║                    工具注册与校验流程                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

                          ┌───────────────────────┐
                          │   tools/__init__.py   │
                          │                       │
                          │   TOOLS = {           │
                          │     "rag"       : rag_tool,        │
                          │     "calculator": calculator_tool, │
                          │     "weather"   : weather_tool,    │
                          │     "db"        : db_tool          │
                          │   }                   │
                          └──────────┬────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │ Agent._register │   │ Validator       │   │ Planner         │
    │ _tools()        │   │ .validate()     │   │ .get_system_    │
    │                 │   │                 │   │ prompt()        │
    │ registry.register│   │ 检查 step["tool"│   │                 │
    │ ("rag",rag_tool)│   │ ] in TOOLS ?    │   │ 在提示词中描述   │
    │                 │   │                 │   │ 可用工具列表     │
    └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
             │                     │                     │
             ▼                     ▼                     ▼
    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
    │ ToolRegistry   │  │ 合法 → 通过    │  │ LLM 看到工具    │
    │ {name→func}    │  │ 非法 → 报错    │  │ 描述,生成 Plan  │
    └────────────────┘  └────────────────┘  └────────────────┘


╔══════════════════════════════════════════════════════════════════════════╗
║              四大工具: 输入 → 处理 → 输出 (详细规格)                       ║
╚══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│  ① calculator_tool.py —— 安全计算器 (AST 白名单)                         │
│                                                                         │
│  入口函数: calculator_tool(expression: str) → 数值                       │
│                                                                         │
│  调用链:                                                                 │
│    calculator_tool("2023+2024")                                          │
│      └── SafeCalculator.calculate("2023+2024")                           │
│            └── ast.parse(expr, mode="eval")   ← 仅允许 eval 模式         │
│                  └── _eval(node) 递归遍历 AST                            │
│                        ├── ast.Constant → node.value                    │
│                        ├── ast.BinOp    → op(left, right)                │
│                        │   OPS = {Add:+, Sub:-, Mult:*, Div:/}          │
│                        └── 其他        → raise ValueError("非法表达式")   │
│                                                                         │
│  输入示例:  "2023+2024"     → 输出: 4047                                 │
│  输入示例:  "(3+5)*2"       → 输出: 16                                   │
│  输入示例:  "os.system()"   → 输出: ValueError (被 AST 白名单阻止)       │
│                                                                         │
│  依赖: ast, operator (标准库)                                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  ② weather_tool.py —— 天气查询 (模拟桩)                                  │
│                                                                         │
│  入口函数: weather_tool(city: str) → str                                 │
│                                                                         │
│  调用链:                                                                 │
│    weather_tool("北京")                                                  │
│      └── return f"{city}天气晴朗 30℃"                                    │
│                                                                         │
│  输入示例:  "北京"       → 输出: "北京天气晴朗 30℃"                       │
│  输入示例:  "上海"       → 输出: "上海天气晴朗 30℃"                       │
│                                                                         │
│  注: 模拟桩, 可替换为真实天气 API 调用                                     │
│  依赖: 无                                                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  ③ rag_tool.py —— RAG 知识检索 (SentenceTransformer + FAISS)             │
│                                                                         │
│  入口函数: rag_tool(query: str) → str                                    │
│                                                                         │
│  调用链:                                                                 │
│    rag_tool("DPO哪年提出")                                               │
│      └── RAGRetriever.search(query="DPO哪年提出", top_k=3)               │
│            ├── model.encode([query])           ← 文本 → 向量 (384维)     │
│            │   model = "paraphrase-multilingual-MiniLM-L12-v2"           │
│            ├── index.search(query_vec, top_k)  ← FAISS 向量相似度检索    │
│            │   index = faiss.read_index("knowledge.index")               │
│            └── chunks[idx].strip()              ← 取回原始文本片段        │
│                 chunks = pickle.load("chunks.pkl")                       │
│                                                                         │
│  输入示例:  "DPO哪年提出"                                                 │
│  内部过程:  query → [0.12, -0.34, ...] → FAISS.search → [3, 7, 1]       │
│  输出示例:  "DPO由Rafael Rafailov等人于2023年提出\n"                      │
│             "DPO是一种直接偏好优化算法\n..."                              │
│                                                                         │
│  依赖: sentence_transformers, numpy, faiss, pickle                       │
│  数据文件: tools/chunks.pkl (文本片段), tools/knowledge.index (FAISS索引) │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  ④ db_tool.py —— 数据库查询工具                                          │
│                                                                         │
│  入口函数: db_tool(sql: str) → str                                       │
│                                                                         │
│  调用链:                                                                 │
│    db_tool("SELECT COUNT(*) FROM execution_logs")                        │
│      └── LogRepository.execute_query(sql)                                │
│            └── conn.execute(sql)           ← SQLite 直接执行             │
│                  └── cursor.fetchall()     → list[tuple]                 │
│                       └── str(rows)        → 转为字符串返回              │
│                                                                         │
│  输入示例:  "SELECT COUNT(*) FROM execution_logs"                        │
│  输出示例:  "[(15,)]"     (15条历史记录)                                  │
│                                                                         │
│  输入示例:  "SELECT * FROM execution_logs WHERE id=1"                    │
│  输出示例:  "[(1, 'DPO哪年提出?', '[{...}]', '[{...}]', 'DPO...')]"      │
│                                                                         │
│  异常处理:  SQL 执行失败 → "SQL执行失败: {error_message}"                  │
│                                                                         │
│  依赖: persistence.log_repository.LogRepository                          │
└─────────────────────────────────────────────────────────────────────────┘


╔══════════════════════════════════════════════════════════════════════════╗
║               新工具添加指南                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

    ① 在 tools/ 下新建 your_tool.py
    ② 实现工具函数: def your_tool(input_str: str) → str
    ③ 在本文件 (tools/__init__.py) 中:
         from .your_tool import your_tool
         TOOLS["your_tool"] = your_tool
    ④ 在 orchestration/planner.py 的 get_system_prompt() 中添加工具描述
    ⑤ 在 orchestration/agent.py 的 _register_tools() 中注册:
         from tools.your_tool import your_tool
         self.tool_registry.register("your_tool", your_tool)
"""
from .rag_tool import rag_tool
from .calculator_tool import calculator_tool
from .weather_tool import weather_tool
from .db_tool import db_tool
from .web_search_tool import web_search_tool

TOOLS = {
    "rag": rag_tool,
    "calculator": calculator_tool,
    "weather": weather_tool,
    "db": db_tool,
    "web_search": web_search_tool,
}