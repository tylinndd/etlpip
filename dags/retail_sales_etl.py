from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from retail_forecast_etl.orchestration import (
    log_task_failure,
    run_ingestion_task,
    run_processing_task,
    run_validation_task,
    run_warehouse_load_task,
)

DAG_ID = "retail_sales_forecasting_etl"

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": log_task_failure,
}

DAG_DOC_MD = """
# Retail Sales Forecasting ETL

Runs the local retail forecasting pipeline in dependency order:

1. Download the configured KaggleHub dataset into `data/raw`.
2. Clean, merge, and engineer features into `data/processed`.
3. Validate processed outputs with Pydantic and Great Expectations.
4. Replace analytics-ready PostgreSQL warehouse tables.

Validation and warehouse loading raise explicit exceptions on critical failures, so Airflow
will stop downstream tasks and mark the run failed.
"""


@dag(
    dag_id=DAG_ID,
    description="Retail sales forecasting ETL pipeline: ingest, process, validate, load.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    doc_md=DAG_DOC_MD,
    tags=["retail", "etl", "forecasting"],
)
def retail_sales_forecasting_etl() -> None:
    @task(task_id="ingest_kaggle_dataset", execution_timeout=timedelta(minutes=20))
    def ingest() -> list[str]:
        return run_ingestion_task()

    @task(task_id="process_raw_data", execution_timeout=timedelta(minutes=20))
    def process() -> list[str]:
        return run_processing_task()

    @task(task_id="validate_processed_data", execution_timeout=timedelta(minutes=20))
    def validate() -> list[str]:
        return run_validation_task()

    @task(task_id="load_postgresql_warehouse", execution_timeout=timedelta(minutes=30))
    def load() -> dict[str, int]:
        return run_warehouse_load_task()

    ingest() >> process() >> validate() >> load()


retail_sales_forecasting_etl()
