from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
)

FORECASTING_TABLE = "retail_sales_features"
STORE_WEEKLY_TABLE = "store_weekly_sales"


def build_metadata(schema: str | None) -> MetaData:
    return MetaData(schema=schema or None)


def define_retail_sales_features(metadata: MetaData) -> Table:
    return Table(
        FORECASTING_TABLE,
        metadata,
        Column("store_id", Integer, primary_key=True),
        Column("department", Integer, primary_key=True),
        Column("sale_date", Date, primary_key=True),
        Column("weekly_sales", Numeric(14, 2), nullable=False),
        Column("sales_amount", Numeric(14, 2), nullable=False),
        Column("store_type", String(10), nullable=False),
        Column("store_size", Integer, nullable=False),
        Column("region", String(50), nullable=False),
        Column("temperature", Numeric(8, 2)),
        Column("fuel_price", Numeric(8, 2)),
        Column("markdown_1", Numeric(14, 2)),
        Column("markdown_2", Numeric(14, 2)),
        Column("markdown_3", Numeric(14, 2)),
        Column("markdown_4", Numeric(14, 2)),
        Column("markdown_5", Numeric(14, 2)),
        Column("markdown_total", Numeric(14, 2), nullable=False),
        Column("cpi", Numeric(10, 2)),
        Column("unemployment", Numeric(8, 2)),
        Column("is_holiday", Boolean, nullable=False),
        Column("holiday_name", String(100), nullable=False),
        Column("season", String(20), nullable=False),
        Column("year", Integer, nullable=False),
        Column("quarter", Integer, nullable=False),
        Column("month", Integer, nullable=False),
        Column("week_of_year", Integer, nullable=False),
        Column("day_of_week", Integer, nullable=False),
        Column("is_month_start", Boolean, nullable=False),
        Column("is_month_end", Boolean, nullable=False),
        Column("sales_lag_1_week", Numeric(14, 2)),
        Column("sales_lag_4_weeks", Numeric(14, 2)),
        Column("sales_rolling_4_week_avg", Numeric(14, 2)),
        Column("sales_rolling_12_week_avg", Numeric(14, 2)),
        Column("store_department_sales_rank", Numeric(8, 2)),
        Index("ix_retail_sales_features_sale_date", "sale_date"),
        Index("ix_retail_sales_features_store_date", "store_id", "sale_date"),
        Index("ix_retail_sales_features_department", "department"),
        Index("ix_retail_sales_features_region_date", "region", "sale_date"),
    )


def define_store_weekly_sales(metadata: MetaData) -> Table:
    return Table(
        STORE_WEEKLY_TABLE,
        metadata,
        Column("store_id", Integer, primary_key=True),
        Column("sale_date", Date, primary_key=True),
        Column("weekly_sales", Numeric(14, 2), nullable=False),
        Column("department_count", Integer, nullable=False),
        Column("is_holiday", Boolean, nullable=False),
        Column("markdown_total", Numeric(14, 2), nullable=False),
        Column("temperature", Numeric(8, 2)),
        Column("fuel_price", Numeric(8, 2)),
        Column("cpi", Numeric(10, 2)),
        Column("unemployment", Numeric(8, 2)),
        Column("store_type", String(10), nullable=False),
        Column("store_size", Integer, nullable=False),
        Column("region", String(50), nullable=False),
        Column("holiday_name", String(100), nullable=False),
        Column("season", String(20), nullable=False),
        Column("sales_amount", Numeric(14, 2), nullable=False),
        Column("year", Integer, nullable=False),
        Column("quarter", Integer, nullable=False),
        Column("month", Integer, nullable=False),
        Column("week_of_year", Integer, nullable=False),
        Column("day_of_week", Integer, nullable=False),
        Column("is_month_start", Boolean, nullable=False),
        Column("is_month_end", Boolean, nullable=False),
        Column("store_sales_lag_1_week", Numeric(14, 2)),
        Column("store_sales_rolling_4_week_avg", Numeric(14, 2)),
        Index("ix_store_weekly_sales_sale_date", "sale_date"),
        Index("ix_store_weekly_sales_store_date", "store_id", "sale_date"),
        Index("ix_store_weekly_sales_region_date", "region", "sale_date"),
    )


def define_warehouse_tables(schema: str | None) -> tuple[MetaData, Table, Table]:
    metadata = build_metadata(schema)
    forecasting_table = define_retail_sales_features(metadata)
    store_weekly_table = define_store_weekly_sales(metadata)
    return metadata, forecasting_table, store_weekly_table
