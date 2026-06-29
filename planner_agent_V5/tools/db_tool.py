import sys
import os

# 把项目根目录（planner_agent_V4）加入导入搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repository.log_repository import LogRepository

repo = LogRepository()

def db_tool(sql):
    try:
        result = repo.execute_query(sql)
        return str(result)
    except Exception as e:
        return f"SQL执行失败: {e}"