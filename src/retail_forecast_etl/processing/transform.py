from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)

SALES_FILE = "sales.csv"
FEATURES_FILE = "features.csv"
STORES_FILE = "stores.csv"

PROCESSED_SALES_FILE = "sales_clean.csv"
PROCESSED_FEATURES_FILE = "features_clean.csv"
PROCESSED_STORES_FILE = "stores_clean.csv"
FORECASTING_FILE = "retail_sales_features.csv"
STORE_WEEKLY_FILE = "store_weekly_sales.csv"

SALES_REQUIRED_COLUMNS = {"store_id", "department", "date", "weekly_sales", "is_holiday"}
FEATURES_REQUIRED_COLUMNS = {
    "store_id",
    "date",
    "temperature",
    "fuel_price",
    "cpi",
    "unemployment",
    "is_holiday",
}
STORES_REQUIRED_COLUMNS = {"store_id", "store_type", "store_size", "region"}
MARKDOWN_COLUMNS = [f"markdown_{index}" for index in range(1, 6)]


class ProcessingError(RuntimeError):
    """Raised when raw data cannot be transformed into processed outputs."""


def process_raw_data(settings: Settings | None = None) -> list[Path]:
    """Clean raw retail CSV files and create analytics-ready processed outputs."""
    settings = settings or get_settings()
    raw_data_dir = settings.raw_data_dir.expanduser()
    processed_data_dir = settings.processed_data_dir.expanduser()
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting raw data processing from %s", raw_data_dir)

    sales = load_sales(raw_data_dir / SALES_FILE)
    features = load_features(raw_data_dir / FEATURES_FILE)
    stores = load_stores(raw_data_dir / STORES_FILE)
    forecasting = build_forecasting_dataset(sales, features, stores)
    store_weekly_sales = build_store_weekly_sales(forecasting)

    outputs = {
        PROCESSED_SALES_FILE: sales,
        PROCESSED_FEATURES_FILE: features,
        PROCESSED_STORES_FILE: stores,
        FORECASTING_FILE: forecasting,
        STORE_WEEKLY_FILE: store_weekly_sales,
    }

    output_paths: list[Path] = []
    for file_name, dataframe in outputs.items():
        output_path = processed_data_dir / file_name
        dataframe.to_csv(output_path, index=False)
        logger.info("Wrote %s row(s) to %s", len(dataframe), output_path)
        output_paths.append(output_path)

    logger.info("Processing completed with %s output file(s)", len(output_paths))
    return output_paths


def load_sales(path: Path) -> pd.DataFrame:
    _require_file(path)
    sales = pd.read_csv(path)
    sales = normalize_column_names(sales)
    _require_columns(sales, SALES_REQUIRED_COLUMNS, path)

    sales["store_id"] = _to_integer(sales["store_id"], "store_id")
    sales["department"] = _to_integer(sales["department"], "department")
    sales["sale_date"] = _to_datetime(sales["date"], "date")
    sales["weekly_sales"] = _to_numeric(sales["weekly_sales"], "weekly_sales").clip(lower=0)
    sales["sales_amount"] = sales["weekly_sales"]
    sales["is_holiday"] = _to_boolean(sales["is_holiday"])

    sales = sales.drop(columns=["date"])
    sales = sales.drop_duplicates(subset=["store_id", "department", "sale_date"], keep="last")
    sales = sales.sort_values(["store_id", "department", "sale_date"]).reset_index(drop=True)
    return sales[
        ["store_id", "department", "sale_date", "weekly_sales", "sales_amount", "is_holiday"]
    ]


def load_features(path: Path) -> pd.DataFrame:
    _require_file(path)
    features = pd.read_csv(path)
    features = normalize_column_names(features)
    _require_columns(features, FEATURES_REQUIRED_COLUMNS, path)

    features["store_id"] = _to_integer(features["store_id"], "store_id")
    features["sale_date"] = _to_datetime(features["date"], "date")
    features["temperature"] = _to_numeric(features["temperature"], "temperature")
    features["fuel_price"] = _to_numeric(features["fuel_price"], "fuel_price")
    features["cpi"] = _to_numeric(features["cpi"], "cpi")
    features["unemployment"] = _to_numeric(features["unemployment"], "unemployment")
    features["is_holiday"] = _to_boolean(features["is_holiday"])

    for column in MARKDOWN_COLUMNS:
        if column not in features.columns:
            features[column] = 0.0
        features[column] = _to_numeric(features[column], column).fillna(0.0).clip(lower=0)

    features["markdown_total"] = features[MARKDOWN_COLUMNS].sum(axis=1)

    if "holiday_name" not in features.columns:
        features["holiday_name"] = "None"
    features["holiday_name"] = _clean_text(features["holiday_name"]).fillna("None")

    if "season" not in features.columns:
        features["season"] = pd.NA
    features["season"] = _clean_text(features["season"])

    features = features.drop(columns=["date"])
    features = features.drop_duplicates(subset=["store_id", "sale_date"], keep="last")
    features = features.sort_values(["store_id", "sale_date"]).reset_index(drop=True)

    return features[
        [
            "store_id",
            "sale_date",
            "temperature",
            "fuel_price",
            *MARKDOWN_COLUMNS,
            "markdown_total",
            "cpi",
            "unemployment",
            "is_holiday",
            "holiday_name",
            "season",
        ]
    ]


def load_stores(path: Path) -> pd.DataFrame:
    _require_file(path)
    stores = pd.read_csv(path)
    stores = normalize_column_names(stores)
    _require_columns(stores, STORES_REQUIRED_COLUMNS, path)

    stores["store_id"] = _to_integer(stores["store_id"], "store_id")
    stores["store_type"] = _clean_text(stores["store_type"])
    stores["store_size"] = _to_integer(stores["store_size"], "store_size")
    stores["region"] = _clean_text(stores["region"])

    stores = stores.drop_duplicates(subset=["store_id"], keep="last")
    stores = stores.sort_values(["store_id"]).reset_index(drop=True)
    return stores[["store_id", "store_type", "store_size", "region"]]


def build_forecasting_dataset(
    sales: pd.DataFrame,
    features: pd.DataFrame,
    stores: pd.DataFrame,
) -> pd.DataFrame:
    merged = sales.merge(
        stores,
        on="store_id",
        how="left",
        validate="many_to_one",
    )
    merged = merged.merge(
        features,
        on=["store_id", "sale_date"],
        how="left",
        suffixes=("_sales", "_features"),
        validate="many_to_one",
    )

    merged["is_holiday"] = merged["is_holiday_features"].combine_first(
        merged["is_holiday_sales"]
    )
    merged = merged.drop(columns=["is_holiday_sales", "is_holiday_features"])

    merged = add_date_features(merged)
    merged = add_sales_features(merged)

    for column in ["store_type", "region", "season", "holiday_name"]:
        if column in merged.columns:
            merged[column] = _clean_text(merged[column])

    numeric_defaults = {
        "temperature": 0.0,
        "fuel_price": 0.0,
        "cpi": 0.0,
        "unemployment": 0.0,
        "markdown_total": 0.0,
        **{column: 0.0 for column in MARKDOWN_COLUMNS},
    }
    merged = merged.fillna(value=numeric_defaults)
    merged["holiday_name"] = merged["holiday_name"].fillna("None")
    merged["season"] = merged["season"].fillna("Unknown")

    ordered_columns = [
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
        *MARKDOWN_COLUMNS,
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
        "is_month_start",
        "is_month_end",
        "sales_lag_1_week",
        "sales_lag_4_weeks",
        "sales_rolling_4_week_avg",
        "sales_rolling_12_week_avg",
        "store_department_sales_rank",
    ]
    return merged[ordered_columns].sort_values(
        ["store_id", "department", "sale_date"]
    ).reset_index(drop=True)


def build_store_weekly_sales(forecasting: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        forecasting.groupby(["store_id", "sale_date"], as_index=False)
        .agg(
            weekly_sales=("weekly_sales", "sum"),
            department_count=("department", "nunique"),
            is_holiday=("is_holiday", "max"),
            markdown_total=("markdown_total", "max"),
            temperature=("temperature", "max"),
            fuel_price=("fuel_price", "max"),
            cpi=("cpi", "max"),
            unemployment=("unemployment", "max"),
            store_type=("store_type", "first"),
            store_size=("store_size", "first"),
            region=("region", "first"),
            holiday_name=("holiday_name", "first"),
            season=("season", "first"),
        )
        .sort_values(["store_id", "sale_date"])
        .reset_index(drop=True)
    )
    grouped["sales_amount"] = grouped["weekly_sales"]
    grouped = add_date_features(grouped)
    grouped["store_sales_lag_1_week"] = grouped.groupby("store_id")["weekly_sales"].shift(1)
    grouped["store_sales_rolling_4_week_avg"] = grouped.groupby("store_id")[
        "weekly_sales"
    ].transform(lambda series: series.shift(1).rolling(window=4, min_periods=1).mean())
    return grouped


def add_date_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    result["year"] = result["sale_date"].dt.year
    result["quarter"] = result["sale_date"].dt.quarter
    result["month"] = result["sale_date"].dt.month
    result["week_of_year"] = result["sale_date"].dt.isocalendar().week.astype("int64")
    result["day_of_week"] = result["sale_date"].dt.dayofweek
    result["is_month_start"] = result["sale_date"].dt.is_month_start
    result["is_month_end"] = result["sale_date"].dt.is_month_end
    return result


def add_sales_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.sort_values(["store_id", "department", "sale_date"]).copy()
    grouped_sales = result.groupby(["store_id", "department"])["weekly_sales"]
    result["sales_lag_1_week"] = grouped_sales.shift(1)
    result["sales_lag_4_weeks"] = grouped_sales.shift(4)
    result["sales_rolling_4_week_avg"] = grouped_sales.transform(
        lambda series: series.shift(1).rolling(window=4, min_periods=1).mean()
    )
    result["sales_rolling_12_week_avg"] = grouped_sales.transform(
        lambda series: series.shift(1).rolling(window=12, min_periods=1).mean()
    )
    result["store_department_sales_rank"] = result.groupby(["store_id", "sale_date"])[
        "weekly_sales"
    ].rank(method="dense", ascending=False)
    return result


def normalize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    result.columns = [
        column.strip().lower().replace(" ", "_").replace("-", "_")
        for column in result.columns
    ]
    return result


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise ProcessingError(f"Required raw file not found: {path}")


def _require_columns(dataframe: pd.DataFrame, required_columns: set[str], path: Path) -> None:
    missing_columns = sorted(required_columns - set(dataframe.columns))
    if missing_columns:
        raise ProcessingError(
            f"{path} is missing required column(s): {', '.join(missing_columns)}"
        )


def _to_integer(series: pd.Series, column_name: str) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    if converted.isna().any():
        raise ProcessingError(f"Column '{column_name}' contains non-integer values.")
    return converted.astype("int64")


def _to_numeric(series: pd.Series, column_name: str) -> pd.Series:
    converted = pd.to_numeric(series, errors="coerce")
    if converted.isna().all():
        raise ProcessingError(f"Column '{column_name}' does not contain numeric values.")
    return converted


def _to_datetime(series: pd.Series, column_name: str) -> pd.Series:
    converted = pd.to_datetime(series, errors="coerce")
    if converted.isna().any():
        raise ProcessingError(f"Column '{column_name}' contains invalid date values.")
    return converted


def _to_boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "t", "yes", "y"})


def _clean_text(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip()
    return cleaned.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
