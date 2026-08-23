import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def main():
    """
    Stream Execution Environment 생성 및 Checkpoint 설정한다.
    Iceberg Sink는 Flink Checkpoint 주기에 따라 MinIO로 커밋을 수행하며 (기본 주기를 10초로 지정했다.)
    """
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(10000)

    t_env = StreamTableEnvironment.create(env)

    # Iceberg 카탈로그 생성 : (Hadoop Catalog + MinIO S3 API)
    t_env.execute_sql("""
        CREATE CATALOG iceberg_catalog WITH (
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
        CREATE TABLE IF NOT EXISTS intelligence.raw_events_iceberg (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at STRING,
            processed_at TIMESTAMP(3)
        ) WITH (
            'format-version'='2',
            'write.upsert.enabled'='true'
        )
    """)

    # Kafka Source Table => Default Catalog의 Temporary Table로 생성
    t_env.execute_sql("""
        CREATE TEMPORARY TABLE kafka_source (
            event_id STRING,
            source STRING,
            category STRING,
            title STRING,
            content STRING,
            created_at STRING,
            proc_time AS PROCTIME()
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'raw-intelligence-stream',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'iceberg-sink-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    print("Starting Streaming Ingestion: Kafka -> Apache Iceberg (MinIO)...")

    statement_set = t_env.create_statement_set()
    statement_set.add_insert_sql("""
        INSERT INTO intelligence.raw_events_iceberg
        SELECT
            event_id,
            source,
            category,
            title,
            content,
            created_at,
            CURRENT_TIMESTAMP AS processed_at
        FROM kafka_source
        WHERE event_id IS NOT NULL
    """)

    job_result = statement_set.execute()
    print(f"Job Submitted. Job ID: {job_result.get_job_client().get_job_id()}")

if __name__ == '__main__':
    main()
