from database.db import conn


def db_tool(query: str):
    """
    数据库查询工具：查询执行日志记录
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question, answer FROM execution_logs ORDER BY id DESC LIMIT 5"
    )
    rows = cursor.fetchall()

    if not rows:
        return "暂无历史记录"

    results = []
    for row in rows:
        results.append(f"[{row[0]}] Q: {row[1]} → A: {row[2]}")

    return "\n".join(results)