from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# ─────────────────────────────────────────
# TASK CALLABLES
# Imports are INSIDE each function — this is intentional.
# Airflow parses this file every 30 seconds to find DAGs.
# If imports are at the top level and fail, the whole DAG breaks.
# Putting imports inside functions means they only run when
# the task actually executes — much safer.
# ─────────────────────────────────────────


def extract_callable():
    sys.path.insert(0, '/opt/airflow/scripts')
    os.chdir('/opt/airflow')
    from extract import run_extract
    run_extract()


def transform_callable():
    sys.path.insert(0, '/opt/airflow/scripts')
    os.chdir('/opt/airflow')
    from transform import run_transform
    run_transform()


def load_callable():
    sys.path.insert(0, '/opt/airflow/scripts')
    os.chdir('/opt/airflow')
    from load import run_load
    run_load()


# ─────────────────────────────────────────
# DAG DEFINITION
# ─────────────────────────────────────────

default_args = {
    "owner": "isuru",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="weather_pipeline",
    description="Hourly weather ETL for 6 cities",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["weather", "etl"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_weather",
        python_callable=extract_callable,
    )

    transform_task = PythonOperator(
        task_id="transform_weather",
        python_callable=transform_callable,
    )

    load_task = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_callable,
    )

    extract_task >> transform_task >> load_task
