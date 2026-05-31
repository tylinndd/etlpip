from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pandas as pd
from sqlalchemy import Engine, create_engine, delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateSchema

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger
from retail_forecast_etl.warehouse.db import build_database_url
from retail_forecast_etl.warehouse.schema import (
    FORECASTING_TABLE,
    STORE_WEEKLY_TABLE,
    define_warehouse_tables,
)

logger = get_logger(__name__)

FORECASTING_FILE = "retail_sales_features.csv"
STORE_WEEKLY_FILE = "store_weekly_sales.csv"
FORECASTING_REPORT = "retail_sales_features_validation_report.json"
STORE_WEEKLY_REPORT = "store_weekly_sales_validation_report.json"
LoadStrategy = Literal["replace"]


class WarehouseLoadError(RuntimeError):
    """Raised when validated data cannot be loaded into the warehouse."""


def load_validated_data(
    settings: Settings | None = None,
    *,
    engine: Engine | None = None,
    load_strategy: LoadStrategy = "replace",
    require_validation_reports: bool = True,
    chunk_size: int = 10_000,
) -> dict[str, int]:
    """Load validated processed datasets into analytics warehouse tables.

    The initial supported strategy is `replace`: inside one transaction the target tables
    are cleared and reloaded from the latest processed CSVs.
    """
    settings = settings or get_settings()
    if load_strategy != "replace":
        raise WarehouseLoadError(f"Unsupported warehouse load strategy: {load_strategy}")

    if require_validation_reports:
        _require_successful_validation_reports(settings.validation_output_dir.expanduser())

    processed_data_dir = settings.processed_data_dir.expanduser()
    forecasting = _read_processed_dataset(processed_data_dir / FORECASTING_FILE)
    store_weekly = _read_processed_dataset(processed_data_dir / STORE_WEEKLY_FILE)

    managed_engine = engine is None
    engine = engine or create_engine(build_database_url(settings), future=True)
    schema = settings.postgres_schema or None
    metadata, forecasting_table, store_weekly_table = define_warehouse_tables(schema)

    logger.info(
        "Loading warehouse data into schema '%s' using '%s' strategy",
        schema or "<default>",
        load_strategy,
    )

    try:
        with engine.begin() as connection:
            _prepare_schema(connection, schema)
            metadata.create_all(connection)

            logger.info("Replacing data in %s", _qualified_name(schema, FORECASTING_TABLE))
            connection.execute(delete(forecasting_table))
            _insert_dataframe(connection, forecasting_table, forecasting, chunk_size)

            logger.info("Replacing data in %s", _qualified_name(schema, STORE_WEEKLY_TABLE))
            connection.execute(delete(store_weekly_table))
            _insert_dataframe(connection, store_weekly_table, store_weekly, chunk_size)

            _assert_loaded_row_count(connection, forecasting_table, len(forecasting))
            _assert_loaded_row_count(connection, store_weekly_table, len(store_weekly))
    except (SQLAlchemyError, OSError, ValueError) as exc:
        raise WarehouseLoadError(f"Warehouse load failed: {exc}") from exc
    finally:
        if managed_engine:
            engine.dispose()

    row_counts = {
        FORECASTING_TABLE: len(forecasting),
        STORE_WEEKLY_TABLE: len(store_weekly),
    }
    for table_name, row_count in row_counts.items():
        logger.info("Loaded %s row(s) into %s", row_count, _qualified_name(schema, table_name))
    return row_counts


def _require_successful_validation_reports(validation_output_dir: Path) -> None:
    report_paths = [
        validation_output_dir / FORECASTING_REPORT,
        validation_output_dir / STORE_WEEKLY_REPORT,
    ]
    missing_reports = [path for path in report_paths if not path.is_file()]
    if missing_reports:
        missing = ", ".join(str(path) for path in missing_reports)
        raise WarehouseLoadError(
            f"Validation report(s) are missing: {missing}. Run validation before loading."
        )

    failed_reports: list[str] = []
    for path in report_paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        pydantic_success = bool(report.get("pydantic", {}).get("success"))
        gx_success = bool(report.get("great_expectations", {}).get("success"))
        if not (pydantic_success and gx_success):
            failed_reports.append(str(path))

    if failed_reports:
        failed = ", ".join(failed_reports)
        raise WarehouseLoadError(f"Validation report(s) contain failures: {failed}")


def _read_processed_dataset(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise WarehouseLoadError(f"Required processed dataset not found: {path}")

    dataframe = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if dataframe.empty:
        raise WarehouseLoadError(f"Processed dataset is empty: {path}")

    dataframe["sale_date"] = pd.to_datetime(dataframe["sale_date"], errors="raise").dt.date
    for column in dataframe.select_dtypes(include=["bool"]).columns:
        dataframe[column] = dataframe[column].astype(bool)
    return dataframe


def _prepare_schema(connection, schema: str | None) -> None:
    if not schema:
        return

    if connection.dialect.name == "postgresql":
        connection.execute(CreateSchema(schema, if_not_exists=True))
        return

    if connection.dialect.name != "sqlite":
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


def _insert_dataframe(connection, table, dataframe: pd.DataFrame, chunk_size: int) -> None:
    table_columns = [column.name for column in table.columns]
    missing_columns = sorted(set(table_columns) - set(dataframe.columns))
    if missing_columns:
        raise WarehouseLoadError(
            f"{table.name} load is missing required column(s): {', '.join(missing_columns)}"
        )

    ordered = dataframe[table_columns]
    records = ordered.where(pd.notna(ordered), None).to_dict("records")
    for start in range(0, len(records), chunk_size):
        batch = records[start : start + chunk_size]
        connection.execute(table.insert(), batch)
        logger.info("Inserted %s row(s) into %s", len(batch), table.name)


def _assert_loaded_row_count(connection, table, expected_count: int) -> None:
    actual_count = connection.execute(
        text(f"SELECT COUNT(*) FROM {_table_sql_name(connection, table)}")
    ).scalar_one()
    if actual_count != expected_count:
        raise WarehouseLoadError(
            f"{table.name} row count mismatch after load: expected {expected_count}, got {actual_count}"
        )


def _table_sql_name(connection, table) -> str:
    preparer = connection.dialect.identifier_preparer
    if table.schema:
        return f"{preparer.quote_schema(table.schema)}.{preparer.quote(table.name)}"
    return preparer.quote(table.name)


def _qualified_name(schema: str | None, table_name: str) -> str:
    return f"{schema}.{table_name}" if schema else table_name
