"""
Airflow DAG: Generate -> Extract -> Validate -> Spark Transform -> Load -> Report
Each stage is just the corresponding script in src/, run as a separate task so
that if one stage fails, Airflow retries ONLY that stage (not the whole pipeline).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

SRC_DIR = "/opt/airflow/src"  # this is where docker-compose.yml mounts your ./src folder

default_args = {
    "owner": "you",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="hospital_pipeline_dag",
    description="Hospital ELT pipeline: generate -> extract -> validate -> transform -> load",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["hospital", "portfolio"],
) as dag:

    generate = BashOperator(
        task_id="generate_data",
        bash_command=f"cd {SRC_DIR} && python generate_data.py",
    )

    extract = BashOperator(
        task_id="extract_to_raw",
        bash_command=f"cd {SRC_DIR} && python extract.py",
    )

    validate = BashOperator(
        task_id="validate_data_quality",
        bash_command=f"cd {SRC_DIR} && python validate.py",
    )

    spark_transform = BashOperator(
        task_id="spark_transform",
        bash_command=f"cd {SRC_DIR} && python transform_spark.py",
    )

    load = BashOperator(
        task_id="load_to_warehouse",
        bash_command=f"cd {SRC_DIR} && python load.py",
    )

    report = BashOperator(
        task_id="quality_report",
        bash_command="echo 'Pipeline finished — check raw.pipeline_audit for the run status.'",
    )

    generate >> extract >> validate >> spark_transform >> load >> report
