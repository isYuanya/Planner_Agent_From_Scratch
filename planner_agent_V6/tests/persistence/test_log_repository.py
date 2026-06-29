"""
tests/persistence/test_log_repository.py

测试 LogRepository —— save() 和 execute_query(), 使用临时 SQLite。
"""

import json
import pytest
import sys
import os

# 确保项目根在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestLogRepository:
    """LogRepository 完整 CRUD 测试"""

    @pytest.fixture(autouse=True)
    def setup_repo(self, temp_db_conn):
        """用临时数据库替换 persistence.db.conn"""
        import persistence.db as db_mod
        original_conn = db_mod.conn
        db_mod.conn = temp_db_conn
        # 重新导入以获取新的 repo (使用新的 conn)
        import persistence.log_repository as repo_mod
        # 强制重新加载
        import importlib
        importlib.reload(repo_mod)
        self.repo = repo_mod.LogRepository()
        self.conn = temp_db_conn
        yield
        db_mod.conn = original_conn

    def test_save_and_query(self):
        """save 一条记录, 然后 execute_query 查出来"""
        plan = [{"id": "s1", "tool": "rag", "input": "DPO"}]
        trace = [
            {
                "step_id": "s1",
                "tool": "rag",
                "input": "DPO",
                "output": "DPO于2023年提出",
                "success": True,
                "error": None,
            }
        ]
        self.repo.save(
            question="DPO哪年提出？",
            plan=plan,
            trace=trace,
            answer="DPO于2023年提出",
        )

        rows = self.repo.execute_query(
            "SELECT question, plan, trace, answer FROM execution_logs"
        )
        assert len(rows) == 1
        question, plan_json, trace_json, answer = rows[0]
        assert question == "DPO哪年提出？"
        assert answer == "DPO于2023年提出"

        # plan / trace 以 JSON 存储, 反序列化后应一致
        assert json.loads(plan_json) == plan
        assert json.loads(trace_json) == trace

    def test_save_multiple(self):
        """多次 save, 查询应返回多条"""
        for i in range(3):
            self.repo.save(
                question=f"q{i}",
                plan=[{"id": "s1", "tool": "rag", "input": f"test{i}"}],
                trace=[],
                answer=f"a{i}",
            )
        rows = self.repo.execute_query("SELECT COUNT(*) FROM execution_logs")
        assert rows[0][0] == 3

    def test_execute_query_select(self):
        """execute_query 返回 list[tuple]"""
        self.repo.save("q?", [], [{"step_id": "s1", "tool": "calculator", "input": "1+1",
                                    "output": "2", "success": True, "error": None}], "2")
        rows = self.repo.execute_query("SELECT * FROM execution_logs WHERE id=1")
        assert isinstance(rows, list)
        assert len(rows) == 1
        # 验证 id 自增
        row = rows[0]
        assert row[0] == 1  # id

    def test_empty_table(self):
        """空表查询返回空列表"""
        rows = self.repo.execute_query("SELECT * FROM execution_logs")
        assert rows == []

    def test_plan_with_chinese(self):
        """JSON 序列化中文 (ensure_ascii=False)"""
        plan = [{"id": "步骤1", "tool": "rag", "input": "什么是DPO"}]
        self.repo.save(
            question="什么是DPO?",
            plan=plan,
            trace=[],
            answer="DPO是直接偏好优化",
        )
        rows = self.repo.execute_query("SELECT plan FROM execution_logs")
        plan_json = rows[0][0]
        assert "步骤1" in plan_json
        assert "什么是DPO" in plan_json