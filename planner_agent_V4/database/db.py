import sqlite3

import os
DB_PATH = os.path.join(os.path.dirname(__file__), "agent.db")

conn = sqlite3.connect(
    DB_PATH,
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS execution_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    plan TEXT,
    trace TEXT,
    answer TEXT
)
""")

conn.commit()