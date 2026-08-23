from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='daily_dbt_iceberg_dimensional_modeling',
    default_args=default_args,
    description='Spark + dbt Batch Pipeline for Iceberg Dimensional Modeling',
    schedule_interval='0 1 * * *', 
    catchup=False,
    tags=['dbt', 'spark', 'iceberg', 'star-schema', 'batch'],
) as dag:
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command='cd /opt/airflow/orchestration/dbt && dbt deps',
    )

    dbt_run = BashOperator(
        task_id='dbt_run_models',
        bash_command='cd /opt/airflow/orchestration/dbt && dbt run --profiles-dir .',
    )

    dbt_test = BashOperator(
        task_id='dbt_test_models',
        bash_command='cd /opt/airflow/orchestration/dbt && dbt test --profiles-dir .',
    )

    dbt_deps >> dbt_run >> dbt_test


