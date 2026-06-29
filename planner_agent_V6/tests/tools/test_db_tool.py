"""
tests/tools/test_db_tool.py

测试数据库查询工具 —— Mock LogRepository, 验证 SQL 执行和异常处理。

注意: tools/__init__.py 中有 `from .db_tool import db_tool`,
导致 `tools.db_tool` 解析为函数而非模块。
需要用 sys.modules 获取真正的模块对象。
"""

import sys
import pytest
from unittest.mock import Mock


class TestDbTool:
    """db_tool 测试 (直接替换模块级 repo 对象)"""

    @pytest.fixture(autouse=True)
    def setup_mock(self):
        """用 Mock 替换 tools.db_tool 模块中的 repo 对象"""
        db_mod = sys.modules["tools.db_tool"]
        # 保存原始 repo
        original_repo = db_mod.repo
        # 替换为 Mock
        mock_repo = Mock()
        db_mod.repo = mock_repo
        self.mock_repo = mock_repo
        self.mod = db_mod
        yield
        # 恢复
        db_mod.repo = original_repo

    def test_select_count(self):
        self.mock_repo.execute_query.return_value = [(15,)]
        result = self.mod.db_tool("SELECT COUNT(*) FROM execution_logs")
        assert "15" in result

    def test_select_with_condition(self):
        self.mock_repo.execute_query.return_value = [
            (1, "test_question", '[{"id":"s1"}]', '[{"step_id":"s1"}]', "answer")
        ]
        result = self.mod.db_tool("SELECT * FROM execution_logs WHERE id=1")
        assert "test_question" in result

    def test_empty_result(self):
        self.mock_repo.execute_query.return_value = []
        result = self.mod.db_tool("SELECT * FROM execution_logs WHERE id=999")
        assert "[]" in result

    def test_sql_error_handling(self):
        self.mock_repo.execute_query.side_effect = Exception("syntax error")
        result = self.mod.db_tool("INVALID SQL!!!")
        assert "SQL执行失败" in result
        assert "syntax error" in result