import pytest
import psycopg_pool
from psycopg.types.json import Jsonb

DATABASE_URL = "postgresql://test_user:test_password@localhost:5433/signalflow_test"

def test_postgres_checkpoint_persistence():
    with psycopg_pool.ConnectionPool(DATABASE_URL) as pool:
        with pool.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id VARCHAR(255) PRIMARY KEY,
                    state JSONB NOT NULL
                );
            """)

            conn.execute(
                "INSERT INTO checkpoints (thread_id, state) VALUES (%s, %s) "
                "ON CONFLICT (thread_id) DO UPDATE SET state = EXCLUDED.state;",
                ("thread-agent-99", Jsonb({"step": 3, "status": "PENDING_HEALING"}))
            )
            conn.commit()

        with pool.connection() as new_conn:
            cursor = new_conn.execute(
                "SELECT state FROM checkpoints WHERE thread_id = %s;", 
                ("thread-agent-99",)
            )
            row = cursor.fetchone()

            assert row is not None
            state_data = row[0]
            assert state_data["step"] == 3
            assert state_data["status"] == "PENDING_HEALING"
