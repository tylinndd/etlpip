from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from retail_forecast_etl.config import Settings
from retail_forecast_etl.warehouse.db import build_database_url
from retail_forecast_etl.warehouse.schema import FORECASTING_TABLE, STORE_WEEKLY_TABLE


class DashboardDataError(RuntimeError):
    """Raised when dashboard data cannot be read from the warehouse."""


@dataclass(frozen=True)
class DashboardFilters:
    start_date: date | None = None
    end_date: date | None = None
    store_ids: tuple[int, ...] = ()
    regions: tuple[str, ...] = ()
    departments: tuple[int, ...] = ()


def create_dashboard_engine(settings: Settings) -> Engine:
    return create_engine(build_database_url(settings), future=True)


def fetch_filter_options(engine: Engine, schema: str | None) -> dict[str, list[Any]]:
    store_weekly = _qualified_table(schema, STORE_WEEKLY_TABLE)
    forecasting = _qualified_table(schema, FORECASTING_TABLE)

    stores = _read_sql(
        engine,
        f"SELECT DISTINCT store_id FROM {store_weekly} ORDER BY store_id",
    )
    regions = _read_sql(
        engine,
        f"SELECT DISTINCT region FROM {store_weekly} WHERE region IS NOT NULL ORDER BY region",
    )
    departments = _read_sql(
        engine,
        f"SELECT DISTINCT department FROM {forecasting} ORDER BY department",
    )
    return {
        "store_ids": stores["store_id"].astype(int).tolist() if not stores.empty else [],
        "regions": regions["region"].dropna().astype(str).tolist() if not regions.empty else [],
        "departments": (
            departments["department"].astype(int).tolist() if not departments.empty else []
        ),
    }


def fetch_date_bounds(engine: Engine, schema: str | None) -> tuple[date | None, date | None]:
    store_weekly = _qualified_table(schema, STORE_WEEKLY_TABLE)
    result = _read_sql(
        engine,
        f"SELECT MIN(sale_date) AS min_date, MAX(sale_date) AS max_date FROM {store_weekly}",
    )
    if result.empty or pd.isna(result.loc[0, "min_date"]) or pd.isna(result.loc[0, "max_date"]):
        return None, None
    return pd.to_datetime(result.loc[0, "min_date"]).date(), pd.to_datetime(
        result.loc[0, "max_date"]
    ).date()


def fetch_kpis(engine: Engine, schema: str | None, filters: DashboardFilters) -> dict[str, Any]:
    table, where_sql, params, count_expression = _sales_source_for_filters(schema, filters)
    result = _read_sql(
        engine,
        f"""
        SELECT
            {count_expression} AS week_count,
            COUNT(DISTINCT store_id) AS store_count,
            SUM(weekly_sales) AS total_sales,
            AVG(weekly_sales) AS average_weekly_sales,
            MAX(sale_date) AS latest_sale_date
        FROM {table}
        {where_sql}
        """,
        params,
    )
    if result.empty:
        return _empty_kpis()

    row = result.iloc[0]
    if pd.isna(row["total_sales"]):
        return _empty_kpis()

    return {
        "total_sales": float(row["total_sales"]),
        "average_weekly_sales": float(row["average_weekly_sales"]),
        "store_count": int(row["store_count"]),
        "week_count": int(row["week_count"]),
        "latest_sale_date": pd.to_datetime(row["latest_sale_date"]).date(),
    }


def fetch_sales_trend(engine: Engine, schema: str | None, filters: DashboardFilters) -> pd.DataFrame:
    table, where_sql, params, _ = _sales_source_for_filters(schema, filters)
    result = _read_sql(
        engine,
        f"""
        SELECT
            sale_date,
            SUM(weekly_sales) AS weekly_sales
        FROM {table}
        {where_sql}
        GROUP BY sale_date
        ORDER BY sale_date
        """,
        params,
    )
    return _coerce_dates(result, "sale_date")


def fetch_top_stores(
    engine: Engine,
    schema: str | None,
    filters: DashboardFilters,
    limit: int = 10,
) -> pd.DataFrame:
    table, where_sql, params, _ = _sales_source_for_filters(schema, filters)
    params["limit"] = limit
    return _read_sql(
        engine,
        f"""
        SELECT
            store_id,
            region,
            SUM(weekly_sales) AS total_sales
        FROM {table}
        {where_sql}
        GROUP BY store_id, region
        ORDER BY total_sales DESC
        LIMIT :limit
        """,
        params,
    )


def fetch_top_departments(
    engine: Engine,
    schema: str | None,
    filters: DashboardFilters,
    limit: int = 10,
) -> pd.DataFrame:
    forecasting = _qualified_table(schema, FORECASTING_TABLE)
    where_sql, params = _build_forecasting_where(filters)
    params["limit"] = limit
    return _read_sql(
        engine,
        f"""
        SELECT
            department,
            SUM(weekly_sales) AS total_sales
        FROM {forecasting}
        {where_sql}
        GROUP BY department
        ORDER BY total_sales DESC
        LIMIT :limit
        """,
        params,
    )


def fetch_data_freshness(engine: Engine, schema: str | None) -> dict[str, Any]:
    store_weekly = _qualified_table(schema, STORE_WEEKLY_TABLE)
    forecasting = _qualified_table(schema, FORECASTING_TABLE)
    result = _read_sql(
        engine,
        f"""
        SELECT
            (SELECT COUNT(*) FROM {store_weekly}) AS store_weekly_rows,
            (SELECT COUNT(*) FROM {forecasting}) AS forecasting_rows,
            (SELECT MAX(sale_date) FROM {store_weekly}) AS latest_store_week,
            (SELECT MAX(sale_date) FROM {forecasting}) AS latest_forecasting_week
        """,
    )
    if result.empty:
        return {}
    row = result.iloc[0]
    return {
        "store_weekly_rows": int(row["store_weekly_rows"]),
        "forecasting_rows": int(row["forecasting_rows"]),
        "latest_store_week": pd.to_datetime(row["latest_store_week"]).date()
        if pd.notna(row["latest_store_week"])
        else None,
        "latest_forecasting_week": pd.to_datetime(row["latest_forecasting_week"]).date()
        if pd.notna(row["latest_forecasting_week"])
        else None,
    }


def _build_store_where(filters: DashboardFilters) -> tuple[str, dict[str, Any]]:
    return _build_where(filters, include_departments=False)


def _build_forecasting_where(filters: DashboardFilters) -> tuple[str, dict[str, Any]]:
    return _build_where(filters, include_departments=True)


def _sales_source_for_filters(
    schema: str | None,
    filters: DashboardFilters,
) -> tuple[str, str, dict[str, Any], str]:
    if filters.departments:
        table = _qualified_table(schema, FORECASTING_TABLE)
        where_sql, params = _build_forecasting_where(filters)
        count_expression = "COUNT(DISTINCT CAST(store_id AS TEXT) || '-' || CAST(sale_date AS TEXT))"
        return table, where_sql, params, count_expression

    table = _qualified_table(schema, STORE_WEEKLY_TABLE)
    where_sql, params = _build_store_where(filters)
    return table, where_sql, params, "COUNT(*)"


def _build_where(filters: DashboardFilters, *, include_departments: bool) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if filters.start_date:
        clauses.append("sale_date >= :start_date")
        params["start_date"] = filters.start_date
    if filters.end_date:
        clauses.append("sale_date <= :end_date")
        params["end_date"] = filters.end_date
    if filters.store_ids:
        placeholders = _add_sequence_params(params, "store_id", filters.store_ids)
        clauses.append(f"store_id IN ({placeholders})")
    if filters.regions:
        placeholders = _add_sequence_params(params, "region", filters.regions)
        clauses.append(f"region IN ({placeholders})")
    if include_departments and filters.departments:
        placeholders = _add_sequence_params(params, "department", filters.departments)
        clauses.append(f"department IN ({placeholders})")

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def _add_sequence_params(params: dict[str, Any], prefix: str, values: tuple[Any, ...]) -> str:
    placeholders: list[str] = []
    for index, value in enumerate(values):
        key = f"{prefix}_{index}"
        params[key] = value
        placeholders.append(f":{key}")
    return ", ".join(placeholders)


def _qualified_table(schema: str | None, table_name: str) -> str:
    if schema:
        return f"{_quote_identifier(schema)}.{_quote_identifier(table_name)}"
    return _quote_identifier(table_name)


def _quote_identifier(identifier: str) -> str:
    if not identifier.replace("_", "").isalnum():
        raise DashboardDataError(f"Unsafe SQL identifier: {identifier}")
    return f'"{identifier}"'


def _read_sql(engine: Engine, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection, params=params or {})
    except SQLAlchemyError as exc:
        raise DashboardDataError(f"Could not read dashboard data: {exc}") from exc


def _coerce_dates(dataframe: pd.DataFrame, column: str) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe
    result = dataframe.copy()
    result[column] = pd.to_datetime(result[column])
    return result


def _empty_kpis() -> dict[str, Any]:
    return {
        "total_sales": 0.0,
        "average_weekly_sales": 0.0,
        "store_count": 0,
        "week_count": 0,
        "latest_sale_date": None,
    }
