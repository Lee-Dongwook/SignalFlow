import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def main():
    """
    DeDuplication & Data Quality Check View

    1. State Memory Optimization: `table.exec.state.ttl=1h`를 설정하여 1시간 이전의 중복 검증 Key를 State 메모리에서 자동으로 Eviction하도록 관리
    2. Out-of-Order & Duplicate Handling: Kafka 수신 단에서 동일 event_id가 여러번 유입 될 경우, 
                                          Flink SQL의 ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ts ASC) 구문을 활용해
                                          가장 먼저 발생한 1건만 통과 시킴
    3. Data Quality Gate: Null ID, Empty String, Future TimeStamp 등 손상된 이벤트를 In-flight 단계에서 차단 -> Downstream lakehouse/search-engine 데이터 오염 방지

    """
    env = StreamExecutionEnvironment.get_execution_environment()

    env.enable_checkpointing(1000)
    t_env = StreamTableEnvironment.create(env)

    t_env.get_config().get_configuration().set_string("table.exec.state.ttl", "1h")

    t_env.execute_sql("""
        CREATE CATALOG iceberg_catalog WITH(
            'type'='iceberg',
            'catalog-type'='hadoop',
            'warehouse'='s3a://warehouse/',
            'property-version'='1',
            'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
            's3.endpoint'='http://minio:9000',
            's3.path-style-access'='true',
            's3.access-key-id'='admin',
            's3.secret-access-key'='password123'
        )
    """)

    t_env.use_catalog('iceberg_catalog')
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS intelligence")

    t_env.execute_sql("""
        CREATE TABLE IF NOT EXISTS intelligence.valid_events_iceberg (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at STRING,
            processed_at TIMESTAMP(3),
            PRIMARY KEY (event_id) NOT ENFORCED
        ) WITH (
            'format-version'='2',
            'write.upsert.enabled'='true'
        )
    """)

    t_env.execute_sql("""
        CREATE TEMPORARY TABLE kafka_raw_source (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at STRING,
            ts AS TO_TIMESTAMP(REPLACE(SUBSTRING(created_at, 1, 19), 'T', ' ')),
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'raw-intelligence-stream',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'quality-dedup-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)




