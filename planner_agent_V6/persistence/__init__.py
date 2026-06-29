"""
persistence 包 —— 数据持久层 (Data Persistence Layer)
======================================================

本包合并了原来的 database/ 和 repository/ 两个包，统一管理数据库连接
与数据访问逻辑。采用仓库模式 (Repository Pattern) 隔离业务与存储细节。


╔══════════════════════════════════════════════════════════════════════════╗
║                    持久层架构与数据流                                     ║
╚══════════════════════════════════════════════════════════════════════════╝

                      ┌─────────────────────────────┐
                      │    上层调用者                 │
                      └──────────┬──────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  │                  ▼
   ┌──────────────────┐         │       ┌──────────────────┐
   │ orchestration/   │         │       │ tools/db_tool.py │
   │ agent.py         │         │       │                  │
   │                  │         │       │ db_tool(sql)     │
   │ Agent.run() 结束时│         │       │ → LogRepository  │
   │ 调用 save()      │         │       │ .execute_query() │
   └────────┬─────────┘         │       └────────┬─────────┘
            │                   │                │
            ▼                   │                ▼
   ┌────────────────────────────────────────────────────────┐
   │                    LogRepository                        │
   │                    (数据访问层)                          │
   │                                                        │
   │  ① save(question, plan, trace, answer)                  │
   │     │                                                  │
   │     │  序列化: json.dumps(plan, ensure_ascii=False)      │
   │     │         json.dumps(trace, ensure_ascii=False)      │
   │     │                                                  │
   │     │  SQL INSERT:                                      │
   │     │  INSERT INTO execution_logs                       │
   │     │  (question, plan, trace, answer)                  │
   │     │  VALUES (?, ?, ?, ?)                              │
   │     │                                                  │
   │     └── conn.commit()                                   │
   │                                                        │
   │  ② execute_query(sql)                                   │
   │     │                                                  │
   │     │  conn.execute(sql) → cursor                       │
   │     └── cursor.fetchall() → list[tuple]                 │
   │                                                        │
   └──────────────────────┬─────────────────────────────────┘
                          │
                          │ from persistence.db import conn
                          ▼
   ┌────────────────────────────────────────────────────────┐
   │                    db.py (连接层)                        │
   │                                                        │
   │  DB_PATH = os.path.join(__file__, "agent.db")           │
   │           → persistence/agent.db                        │
   │                                                        │
   │  conn = sqlite3.connect(                                │
   │      DB_PATH,                                           │
   │      check_same_thread=False  ← 允许多线程访问          │
   │  )                                                      │
   │                                                        │
   │  CREATE TABLE IF NOT EXISTS execution_logs(             │
   │      id       INTEGER PRIMARY KEY AUTOINCREMENT,        │
   │      question TEXT,                                     │
   │      plan     TEXT,    ← JSON 字符串                     │
   │      trace    TEXT,    ← JSON 字符串                     │
   │      answer   TEXT                                      │
   │  )                                                      │
   │                                                        │
   └──────────────────────┬─────────────────────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   persistence/       │
              │   agent.db           │
              │   (SQLite 文件)       │
              └──────────────────────┘


╔══════════════════════════════════════════════════════════════════════════╗
║                execution_logs 表数据格式示例                               ║
╚══════════════════════════════════════════════════════════════════════════╝

    ┌────┬──────────────────────────────────┬─────────────────────────────┐
    │ id │ question                         │ plan (JSON TEXT)            │
    ├────┼──────────────────────────────────┼─────────────────────────────┤
    │ 1  │ "DPO哪年提出？算2023+2024"        │ '[{"id":"step1","tool":     │
    │    │                                  │   "rag","input":"DPO..."},  │
    │    │                                  │   {"id":"step2","tool":     │
    │    │                                  │   "calculator","input":     │
    │    │                                  │   "2023+{step1}"}]'         │
    ├────┼──────────────────────────────────┼─────────────────────────────┤
    │    │ trace (JSON TEXT)                │ answer                      │
    ├────┼──────────────────────────────────┼─────────────────────────────┤
    │    │ '[{"step_id":"step1","tool":     │ "DPO于2023年由Rafael        │
    │    │   "rag","input":"DPO哪年提出",    │  Rafailov等人提出。          │
    │    │   "output":"DPO...于2023年...",   │  2023+2024=4047。"          │
    │    │   "success":true,"error":null},  │                             │
    │    │  {"step_id":"step2","tool":      │                             │
    │    │   "calculator","input":          │                             │
    │    │   "2023+2024","output":"4047",   │                             │
    │    │   "success":true,"error":null}]' │                             │
    └────┴──────────────────────────────────┴─────────────────────────────┘

    入库前序列化:
        json.dumps(plan,  ensure_ascii=False)  →  "[{"id": "step1", ...}]"
        json.dumps(trace, ensure_ascii=False)  →  "[{"step_id": "step1", ...}]"

    出库查询:
        db_tool("SELECT question FROM execution_logs WHERE id=1")
        → "[(DPO哪年提出？算2023+2024,)]"


╔══════════════════════════════════════════════════════════════════════════╗
║                    设计模式                                              ║
╚══════════════════════════════════════════════════════════════════════════╝

    仓库模式 (Repository Pattern):
        上层 → LogRepository (接口) → db.py (实现) → agent.db (存储)
               ↑ 隔离层              ↑ 底层细节      ↑ 物理文件

    好处:
        - 业务逻辑不直接接触 SQLite 连接
        - 可 Mock LogRepository 进行单元测试
        - 可替换 db.py 以切换数据库 (如 PostgreSQL)
"""
