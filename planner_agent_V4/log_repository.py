import json

from db import conn


class LogRepository:

    def save(
            self,
            question,
            plan,
            trace,
            answer
    ):

        conn.execute(
            """
            INSERT INTO execution_logs
            (
                question,
                plan,
                trace,
                answer
            )
            VALUES
            (
                ?, ?, ?, ?
            )
            """,
            (
                question,
                json.dumps(plan, ensure_ascii=False),
                json.dumps(trace, ensure_ascii=False),
                answer
            )
        )

        conn.commit()