from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator

"""
Small File Problem : Flink 스트리밍 Sink로 발생하는 수 KB단위의 무수한 Small Parquet 파일들을
128MB 크기의 표준 대용량 파티션 파일로 자동 병합 -> Downstream 배치 분석 (Spark/dbt) 및 쿼리 Read 속도 개선

Storage Limit & Expiry Mangement : 스트리밍 특성 상 메타데이터와 파일 변경 내역 (Snapshot)이 무한하게 증가하는 현상을 방지하고자,
24시간 경과된 Old Snapshot & Orphan Files들을 주기적으로 Pruning 하는 유지보수 체계 확립

"""

default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id = 'daily_iceberg_table_compaction',
    default_args=default_args,
    description="Compaction and Maintenance DAG for Iceberg Small Files",
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=["iceberg","compaction","data-lakehouse","quality"],
) as dag:

    CATALOG_NAME = "iceberg_catalog"
    DB_NAME = "intelligence"
    TABLE_NAME = "valid_events_iceberg"

    compact_table_task = SparkSubmitOperator(
        task_id='compact_iceberg_small_files',
        application='/opt/airflow/orchestration/spark_jobs/iceberg_compaction.py',
        conn_id='spark_default',
        packages=(
            'org.apache.iceberg:iceberg-spar-runtime-3.4_2.12:1.4.2'
            'org.apache.hadoop:hadoop-aws:3.3.4,'
            'com.amazonaws:aws-java-sdk-bundle:1.12.261'
        ),
        application_args=[CATALOG_NAME, DB_NAME, TABLE_NAME],
        conf={
            f"spark.sql.catalog.{CATALOG_NAME}": "org.apache.iceberg.spark.SparkCatalog",
            f"spark.sql.catalog.{CATALOG_NAME}.type": "hadoop",
            f"spark.sql.catalog.{CATALOG_NAME}.warehouse": "s3a://warehouse/",
            f"spark.sql.catalog.{CATALOG_NAME}.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
            f"spark.sql.catalog.{CATALOG_NAME}.s3.endpoint": "http://minio:9000",
            f"spark.sql.catalog.{CATALOG_NAME}.s3.path-style-access": "true",
            "spark.hadoop.fs.s3a.access.key": "admin",
            "spark.hadoop.fs.s3a.secret.key": "password123",
            "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
            "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"  
        },
        executor_memory='2g',
        executor_cores=2,
        num_executors=2,
        name='spark_iceberg_compaction_job',
    )

    compact_table_task

