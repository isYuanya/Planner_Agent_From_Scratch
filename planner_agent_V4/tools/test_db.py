from db_tool import db_tool

print(
    db_tool(
        "SELECT COUNT(*) FROM execution_logs"
    )
)