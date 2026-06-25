import sqlite3

conn = sqlite3.connect(
    "agent.db",
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