from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(5000) 
    t_env = StreamTableEnvironment.create(env)

    t_env.execute_sql("""
        CREATE TEMPORARY TABLE kafka_validated_source (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'validated-intelligence-stream',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'clickhouse-sink-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    t_env.execute_sql("""
        CREATE TEMPORARY TABLE clickhouse_sink (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:clickhouse://clickhouse:8123/intelligence',
            'table-name' = 'events_raw',
            'username' = 'default',
            'password' = '',
            'sink.batch.size' = '1000',
            'sink.batch.interval' = '1s',
            'sink.max-retries' = '3'
        )
    """)

    print("Starting Flink -> ClickHouse Pipeline...")

    statement_set = t_env.create_statement_set()
    statement_set.add_insert_sql("""
        INSERT INTO clickhouse_sink
        SELECT 
            event_id,
            source,
            category,
            title,
            content,
            TO_TIMESTAMP(REPLACE(SUBSTRING(created_at, 1, 19), 'T', ' ')) AS created_at
        FROM kafka_validated_source
    """)

    job_result = statement_set.execute()
    print(f"ClickHouse Sink Active. Job ID: {job_result.get_job_client().get_job_id()}")

if __name__ == "__main__":
    main()
