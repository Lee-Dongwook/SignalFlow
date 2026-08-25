from pyflink.datastream.functions import MapFunction
import clickhouse_connect

class ClickHouseVectorSink(MapFunction):
    def __init__(self, host="localhost", port=8123, database="signalflow_test"):
        self.host = host
        self.port = port
        self.database = database
        self.client = None

    def open(self, runtime_context):
        init_client = clickhouse_connect.get_client(host=self.host, port=self.port)
        init_client.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        
        self.client = clickhouse_connect.get_client(
            host=self.host, port=self.port, database=self.database
        )
        self.client.command("""
            CREATE TABLE IF NOT EXISTS intelligence_vectors (
                event_id String,
                source String,
                payload String,
                embedding Array(Float32),
                timestamp Int64,
                trace_id String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, event_id)
        """)

    def map(self, value):
        if not value:
            return value
            
        data = [[
            value.get("event_id", ""),
            value.get("source", ""),
            value.get("payload", ""),
            value.get("embedding", []),
            value.get("timestamp", 0),
            value.get("trace_id", "")
        ]]
        
        self.client.insert(
            "intelligence_vectors",
            data,
            column_names=["event_id", "source", "payload", "embedding", "timestamp", "trace_id"]
        )
        return value

    def close(self):
        if self.client:
            self.client.close()
