from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from retail_forecast_etl.ingestion import ingest_kaggle_dataset
from retail_forecast_etl.processing import process_raw_data
from retail_forecast_etl.validation import validate_processed_data
from retail_forecast_etl.warehouse import load_validated_data


@dag(
    dag_id="retail_sales_forecasting_etl",
    description="Retail sales forecasting ETL scaffold: ingest, process, validate, load.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["retail", "etl", "forecasting"],
)
def retail_sales_forecasting_etl() -> None:
    @task
    def ingest() -> None:
        ingest_kaggle_dataset()

    @task
    def process() -> None:
        process_raw_data()

    @task
    def validate() -> None:
        validate_processed_data()

    @task
    def load() -> None:
        load_validated_data()

    ingest() >> process() >> validate() >> load()


retail_sales_forecasting_etl()
