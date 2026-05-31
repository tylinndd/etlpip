from __future__ import annotations

from pathlib import Path
from typing import Any

from retail_forecast_etl.config import get_settings
from retail_forecast_etl.ingestion import ingest_kaggle_dataset
from retail_forecast_etl.processing import process_raw_data
from retail_forecast_etl.utils.logging import configure_logging, get_logger
from retail_forecast_etl.validation import validate_processed_data
from retail_forecast_etl.warehouse import load_validated_data

logger = get_logger(__name__)


def run_ingestion_task() -> list[str]:
    settings = _configure_task_logging()
    logger.info("Airflow ingestion task started")
    paths = ingest_kaggle_dataset(settings)
    result = _paths_to_strings(paths)
    logger.info("Airflow ingestion task completed with %s raw file(s)", len(result))
    return result


def run_processing_task() -> list[str]:
    settings = _configure_task_logging()
    logger.info("Airflow processing task started")
    paths = process_raw_data(settings)
    result = _paths_to_strings(paths)
    logger.info("Airflow processing task completed with %s processed file(s)", len(result))
    return result


def run_validation_task() -> list[str]:
    settings = _configure_task_logging()
    logger.info("Airflow validation task started")
    paths = validate_processed_data(settings)
    result = _paths_to_strings(paths)
    logger.info("Airflow validation task completed with %s report file(s)", len(result))
    return result


def run_warehouse_load_task() -> dict[str, int]:
    settings = _configure_task_logging()
    logger.info("Airflow warehouse load task started")
    row_counts = load_validated_data(settings)
    logger.info("Airflow warehouse load task completed: %s", row_counts)
    return row_counts


def _configure_task_logging():
    settings = get_settings()
    configure_logging(settings.log_level)
    return settings


def _paths_to_strings(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths]


def log_task_failure(context: dict[str, Any]) -> None:
    task_instance = context.get("task_instance")
    exception = context.get("exception")
    dag_run = context.get("dag_run")
    logger.error(
        "Airflow task failed: dag_id=%s task_id=%s run_id=%s exception=%r",
        getattr(task_instance, "dag_id", None),
        getattr(task_instance, "task_id", None),
        getattr(dag_run, "run_id", None),
        exception,
    )
