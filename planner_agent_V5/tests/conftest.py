"""
tests/conftest.py —— 共享 Fixtures

提供所有测试模块共用的 Mock 对象和测试数据。
"""

import pytest
import sqlite3
import os
import tempfile
from unittest.mock import Mock


# ═══════════════════════════════════════════════════════════════════════════
#  Mock LLM Client (DeepSeek)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_client():
    """
    模拟 DeepSeek (OpenAI 兼容) 客户端。
    返回的 client.chat.completions.create(...) 可被配置。
    """
    client = Mock()
    # 默认 LLM 返回: 一个包含 JSON plan 的字符串
    response = Mock()
    response.choices = [
        Mock(message=Mock(content='[{"id":"step1","tool":"calculator","input":"1+1"}]'))
    ]
    client.chat.completions.create.return_value = response
    return client


# ═══════════════════════════════════════════════════════════════════════════
#  示例 Plan (JSON)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_plan():
    """一个合法的示例计划, 含两步 + 变量引用。"""
    return [
        {"id": "step1", "tool": "calculator", "input": "2023+2024"},
        {"id": "step2", "tool": "weather",    "input": "{step1}"},
    ]


@pytest.fixture
def single_step_plan():
    """单步计划 (无变量引用)。"""
    return [
        {"id": "step1", "tool": "rag", "input": "DPO哪年提出"},
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  SQLite 临时数据库 (用于 persistence 层测试)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_db_conn():
    """
    创建临时 SQLite 数据库, 结构与 persistence/db.py 中的 execution_logs 一致。
    测试结束后自动清理。
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs(
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            plan     TEXT,
            trace    TEXT,
            answer   TEXT
        )
    """)
    conn.commit()
    yield conn
    conn.close()
    os.unlink(path)


# ═══════════════════════════════════════════════════════════════════════════
#  示例执行轨迹 (trace)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_trace():
    """两条完整的执行轨迹条目。"""
    return [
        {
            "step_id": "step1",
            "tool":    "rag",
            "input":   "DPO哪年提出",
            "output":  "DPO由Rafael Rafailov等人于2023年提出",
            "success": True,
            "error":   None,
        },
        {
            "step_id": "step2",
            "tool":    "calculator",
            "input":   "2023+2024",
            "output":  "4047",
            "success": True,
            "error":   None,
        },
    ]