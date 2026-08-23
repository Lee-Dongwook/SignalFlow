import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    t_env = StreamTableEnvironment.create(env)

    # Kafka Source 테이블 정의하기
    t_env.execute_sql("""
        CREATE TABLE raw_events(
            event_id STRING,
            source STRING,
            content STRING,
            created_at TIMESTAMP(3),
            WATERMARK FOR created_at AS created_at - INTERVAL '5' SECOND        
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'raw-intelligence-stream',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'flink-consumer-group',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # ClickHouse Debug
    t_env.execute_sql("""
        CREATE TABLE print_sink(
            event_id STRING,
            source STRING,
            content STRING,
            created_at TIMESTAMP(3)        
        ) WITH (
            'connector' = 'print'
        )
    """)

    # Query Execute 
    t_env.execute_sql("""
        INSERT INTO print_sink
        SELECT event_id, source, content, created_at
        FROM raw_events
        WHERE content IS NOT NULL
    """)

if __name__ == '__main__':
    main()
