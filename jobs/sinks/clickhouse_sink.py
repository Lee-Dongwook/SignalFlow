import os
import clickhouse_connect
from pyflink.datastream.functions import SinkFunction

class ClickHouseVectorSink(SinkFunction):
    def __init__(self, host: str = None, port: int = 8123, database: str = "signalflow_test"):
        self.host = host or os.getenv("CLICKHOUSE_HOST", "host.k3d.internal")
        self.port = port
        self.database = database
        self.client = None
    
    def open(self, context):
        self.client = clickhouse_connect.get_client(
            host=self.host, port=self.port, database=self.database
        )

        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS intelligence_vectors (
                event_id String,
                source String,
                payload String,
                embedding Array(Float32),
                timestamp Int64,
                trace_id String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, event_id)
        """
        )

    def invoke(self, value:dict, context):
        data_row = [
            value["event_id"],
            value["source"],
            value["payload"],
            value["embedding"],
            value["timestamp"],
            value["trace_id"],
        ]
        self.client.insert(
            "intelligence_vectors",
            [data_row],
            column_names=["event_id", "source", "payload", "embedding", "timestamp", "trace_id"],
        )
    
    def close(self):
        if self.client:
            self.client.close()
