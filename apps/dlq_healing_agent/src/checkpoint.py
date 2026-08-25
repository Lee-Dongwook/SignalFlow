import os
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/signalflow_db")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=20,
    kwargs={"autocommit": True}
)

def get_langgraph_checkpointer():
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return checkpointer
