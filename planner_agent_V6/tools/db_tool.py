from persistence.log_repository import LogRepository

repo = LogRepository()

def db_tool(sql):
    try:
        result = repo.execute_query(sql)
        return str(result)
    except Exception as e:
        return f"SQL执行失败: {e}"