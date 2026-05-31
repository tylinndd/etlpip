from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ValidationError as PydanticValidationError

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger
from retail_forecast_etl.validation.models import (
    ForecastingSalesRecord,
    StoreWeeklySalesRecord,
)

logger = get_logger(__name__)

FORECASTING_FILE = "retail_sales_features.csv"
STORE_WEEKLY_FILE = "store_weekly_sales.csv"

FORECASTING_REQUIRED_COLUMNS = {
    "store_id",
    "department",
    "sale_date",
    "weekly_sales",
    "sales_amount",
    "store_type",
    "store_size",
    "region",
    "temperature",
    "fuel_price",
    "markdown_total",
    "cpi",
    "unemployment",
    "is_holiday",
    "holiday_name",
    "season",
    "year",
    "quarter",
    "month",
    "week_of_year",
    "day_of_week",
    "sales_lag_1_week",
    "sales_lag_4_weeks",
    "sales_rolling_4_week_avg",
    "sales_rolling_12_week_avg",
}
STORE_WEEKLY_REQUIRED_COLUMNS = {
    "store_id",
    "sale_date",
    "weekly_sales",
    "department_count",
    "is_holiday",
    "markdown_total",
    "store_type",
    "store_size",
    "region",
    "holiday_name",
    "season",
    "sales_amount",
    "year",
    "quarter",
    "month",
    "week_of_year",
    "day_of_week",
    "store_sales_lag_1_week",
    "store_sales_rolling_4_week_avg",
}
FORECASTING_NON_NULL_COLUMNS = [
    "store_id",
    "department",
    "sale_date",
    "weekly_sales",
    "sales_amount",
    "store_type",
    "store_size",
    "region",
    "is_holiday",
    "year",
    "quarter",
    "month",
    "week_of_year",
    "day_of_week",
]
STORE_WEEKLY_NON_NULL_COLUMNS = [
    "store_id",
    "sale_date",
    "weekly_sales",
    "department_count",
    "sales_amount",
    "store_type",
    "store_size",
    "region",
    "is_holiday",
    "year",
    "quarter",
    "month",
    "week_of_year",
    "day_of_week",
]
STORE_TYPES = ["A", "B", "C"]
REGIONS = ["East", "North", "South", "West"]
SEASONS = ["Fall", "Spring", "Summer", "Winter"]


class DataValidationError(RuntimeError):
    """Raised when processed data fails a critical validation check."""


def validate_processed_data(settings: Settings | None = None) -> list[Path]:
    """Validate processed datasets with Pydantic and Great Expectations."""
    settings = settings or get_settings()
    processed_data_dir = settings.processed_data_dir.expanduser()
    validation_output_dir = settings.validation_output_dir.expanduser()
    validation_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting validation for processed data in %s", processed_data_dir)

    forecasting = _read_processed_csv(processed_data_dir / FORECASTING_FILE)
    store_weekly = _read_processed_csv(processed_data_dir / STORE_WEEKLY_FILE)

    validation_specs = [
        DatasetValidationSpec(
            name="retail_sales_features",
            dataframe=forecasting,
            model=ForecastingSalesRecord,
            required_columns=FORECASTING_REQUIRED_COLUMNS,
            non_null_columns=FORECASTING_NON_NULL_COLUMNS,
            unique_columns=["store_id", "department", "sale_date"],
            numeric_minimums={
                "store_id": 1,
                "department": 1,
                "weekly_sales": 0,
                "sales_amount": 0,
                "store_size": 1,
                "fuel_price": 0,
                "markdown_total": 0,
                "cpi": 0,
                "unemployment": 0,
                "quarter": 1,
                "month": 1,
                "week_of_year": 1,
                "day_of_week": 0,
            },
            numeric_maximums={
                "quarter": 4,
                "month": 12,
                "week_of_year": 53,
                "day_of_week": 6,
            },
        ),
        DatasetValidationSpec(
            name="store_weekly_sales",
            dataframe=store_weekly,
            model=StoreWeeklySalesRecord,
            required_columns=STORE_WEEKLY_REQUIRED_COLUMNS,
            non_null_columns=STORE_WEEKLY_NON_NULL_COLUMNS,
            unique_columns=["store_id", "sale_date"],
            numeric_minimums={
                "store_id": 1,
                "weekly_sales": 0,
                "sales_amount": 0,
                "department_count": 1,
                "store_size": 1,
                "markdown_total": 0,
                "quarter": 1,
                "month": 1,
                "week_of_year": 1,
                "day_of_week": 0,
            },
            numeric_maximums={
                "quarter": 4,
                "month": 12,
                "week_of_year": 53,
                "day_of_week": 6,
            },
        ),
    ]

    report_paths: list[Path] = []
    failures: list[str] = []

    for spec in validation_specs:
        logger.info("Validating %s with %s row(s)", spec.name, len(spec.dataframe))
        pydantic_report = _validate_with_pydantic(spec)
        gx_report = _validate_with_great_expectations(spec)
        report = {
            "dataset": spec.name,
            "row_count": len(spec.dataframe),
            "pydantic": pydantic_report,
            "great_expectations": gx_report,
        }
        report_path = validation_output_dir / f"{spec.name}_validation_report.json"
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        logger.info("Wrote validation report to %s", report_path)
        report_paths.append(report_path)

        if not pydantic_report["success"]:
            failures.append(f"{spec.name} failed Pydantic row validation")
        if not gx_report["success"]:
            failures.append(f"{spec.name} failed Great Expectations validation")

    if failures:
        failure_summary = "; ".join(failures)
        logger.error("Validation failed: %s", failure_summary)
        raise DataValidationError(f"Critical data quality checks failed: {failure_summary}")

    logger.info("Validation completed successfully with %s report file(s)", len(report_paths))
    return report_paths


class DatasetValidationSpec:
    def __init__(
        self,
        *,
        name: str,
        dataframe: pd.DataFrame,
        model: type[BaseModel],
        required_columns: set[str],
        non_null_columns: list[str],
        unique_columns: list[str],
        numeric_minimums: dict[str, int | float],
        numeric_maximums: dict[str, int | float],
    ) -> None:
        self.name = name
        self.dataframe = dataframe
        self.model = model
        self.required_columns = required_columns
        self.non_null_columns = non_null_columns
        self.unique_columns = unique_columns
        self.numeric_minimums = numeric_minimums
        self.numeric_maximums = numeric_maximums


def _read_processed_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise DataValidationError(f"Required processed file not found: {path}")
    dataframe = pd.read_csv(path, keep_default_na=False, na_values=[""])
    if dataframe.empty:
        raise DataValidationError(f"Processed file is empty: {path}")
    return dataframe


def _validate_with_pydantic(spec: DatasetValidationSpec) -> dict[str, Any]:
    _require_columns(spec.dataframe, spec.required_columns, spec.name)
    records = spec.dataframe.where(pd.notna(spec.dataframe), None).to_dict("records")
    errors: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=2):
        try:
            spec.model.model_validate(record)
        except PydanticValidationError as exc:
            errors.append({"row_number": row_number, "errors": exc.errors()})
            if len(errors) >= 20:
                break

    success = not errors
    logger.info(
        "Pydantic validation for %s: %s",
        spec.name,
        "passed" if success else f"failed with {len(errors)} sampled error(s)",
    )
    return {
        "success": success,
        "validated_rows": len(records),
        "error_count": len(errors),
        "errors": errors,
    }


def _validate_with_great_expectations(spec: DatasetValidationSpec) -> dict[str, Any]:
    logging.getLogger("great_expectations").setLevel(logging.WARNING)
    try:
        import great_expectations as gx
        from great_expectations import expectations as gxe
    except ImportError as exc:
        raise DataValidationError(
            "great-expectations is required for validation. Install project requirements."
        ) from exc

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(f"{spec.name}_source")
    asset = data_source.add_dataframe_asset(name=spec.name)
    batch_definition = asset.add_batch_definition_whole_dataframe(f"{spec.name}_batch")

    suite = gx.ExpectationSuite(name=f"{spec.name}_suite")
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=1))

    for column in sorted(spec.required_columns):
        suite.add_expectation(gxe.ExpectColumnToExist(column=column))

    for column in spec.non_null_columns:
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))

    suite.add_expectation(gxe.ExpectCompoundColumnsToBeUnique(column_list=spec.unique_columns))

    for column, minimum in spec.numeric_minimums.items():
        maximum = spec.numeric_maximums.get(column)
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeBetween(
                column=column,
                min_value=minimum,
                max_value=maximum,
            )
        )

    for column, maximum in spec.numeric_maximums.items():
        if column in spec.numeric_minimums:
            continue
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeBetween(column=column, max_value=maximum)
        )

    if "store_type" in spec.dataframe.columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeInSet(column="store_type", value_set=STORE_TYPES)
        )
    if "region" in spec.dataframe.columns:
        suite.add_expectation(gxe.ExpectColumnValuesToBeInSet(column="region", value_set=REGIONS))
    if "season" in spec.dataframe.columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeInSet(column="season", value_set=SEASONS)
        )
    if "sale_date" in spec.dataframe.columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToMatchRegex(column="sale_date", regex=r"^\d{4}-\d{2}-\d{2}$")
        )

    context.suites.add(suite)
    validation_definition = gx.ValidationDefinition(
        name=f"{spec.name}_validation",
        data=batch_definition,
        suite=suite,
    )
    context.validation_definitions.add(validation_definition)
    result = validation_definition.run(batch_parameters={"dataframe": spec.dataframe})
    result_json = result.to_json_dict()
    failed_expectations = [
        {
            "expectation": item["expectation_config"]["type"],
            "kwargs": item["expectation_config"].get("kwargs", {}),
            "success": item["success"],
        }
        for item in result_json.get("results", [])
        if not item.get("success")
    ]

    logger.info(
        "Great Expectations validation for %s: %s",
        spec.name,
        "passed" if result.success else f"failed with {len(failed_expectations)} expectation(s)",
    )
    return {
        "success": bool(result.success),
        "statistics": result_json.get("statistics", {}),
        "failed_expectations": failed_expectations,
    }


def _require_columns(dataframe: pd.DataFrame, required_columns: set[str], dataset_name: str) -> None:
    missing_columns = sorted(required_columns - set(dataframe.columns))
    if missing_columns:
        raise DataValidationError(
            f"{dataset_name} is missing required column(s): {', '.join(missing_columns)}"
        )
