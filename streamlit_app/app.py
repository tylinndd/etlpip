from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from retail_forecast_etl.config import get_settings
from streamlit_app.dashboard_data import (
    DashboardDataError,
    DashboardFilters,
    create_dashboard_engine,
    fetch_data_freshness,
    fetch_date_bounds,
    fetch_filter_options,
    fetch_kpis,
    fetch_sales_trend,
    fetch_top_departments,
    fetch_top_stores,
)


st.set_page_config(page_title="Retail Sales Forecasting", layout="wide")

settings = get_settings()
schema = settings.postgres_schema or None

st.title("Retail Sales Forecasting")
st.caption("PostgreSQL-backed retail sales analytics from the ETL warehouse.")


@st.cache_resource(show_spinner=False)
def get_engine():
    return create_dashboard_engine(settings)


@st.cache_data(ttl=300, show_spinner=False)
def load_filter_options() -> dict[str, list]:
    return fetch_filter_options(get_engine(), schema)


@st.cache_data(ttl=300, show_spinner=False)
def load_date_bounds() -> tuple[date | None, date | None]:
    return fetch_date_bounds(get_engine(), schema)


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_data(filters: DashboardFilters):
    engine = get_engine()
    return {
        "kpis": fetch_kpis(engine, schema, filters),
        "trend": fetch_sales_trend(engine, schema, filters),
        "top_stores": fetch_top_stores(engine, schema, filters),
        "top_departments": fetch_top_departments(engine, schema, filters),
        "freshness": fetch_data_freshness(engine, schema),
    }


def show_empty_state(message: str) -> None:
    st.info(message)
    with st.expander("Warehouse connection settings"):
        st.write(
            {
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "database": settings.postgres_db,
                "schema": settings.postgres_schema or "<default>",
            }
        )


def format_currency(dataframe: pd.DataFrame, column: str) -> pd.DataFrame:
    formatted = dataframe.copy()
    formatted[column] = formatted[column].map(lambda value: f"${value:,.0f}")
    return formatted


try:
    min_date, max_date = load_date_bounds()
    filter_options = load_filter_options()
except DashboardDataError as exc:
    show_empty_state(
        "No warehouse data is available yet. Run ingestion, processing, validation, "
        "and warehouse loading before opening the dashboard."
    )
    st.exception(exc)
    st.stop()

if not min_date or not max_date:
    show_empty_state("The warehouse tables are present but empty.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    selected_dates = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = min_date, max_date

    selected_stores = st.multiselect("Stores", filter_options["store_ids"])
    selected_regions = st.multiselect("Regions", filter_options["regions"])
    selected_departments = st.multiselect("Departments", filter_options["departments"])

    if st.button("Refresh warehouse data"):
        st.cache_data.clear()
        st.rerun()

filters = DashboardFilters(
    start_date=start_date,
    end_date=end_date,
    store_ids=tuple(int(store_id) for store_id in selected_stores),
    regions=tuple(str(region) for region in selected_regions),
    departments=tuple(int(department) for department in selected_departments),
)

try:
    dashboard_data = load_dashboard_data(filters)
except DashboardDataError as exc:
    show_empty_state("The dashboard could not query the warehouse with the selected filters.")
    st.exception(exc)
    st.stop()

kpis = dashboard_data["kpis"]
trend = dashboard_data["trend"]
top_stores = dashboard_data["top_stores"]
top_departments = dashboard_data["top_departments"]
freshness = dashboard_data["freshness"]

if kpis["week_count"] == 0:
    st.warning("No sales rows match the selected filters.")
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric("Total Sales", f"${kpis['total_sales']:,.0f}")
metric_columns[1].metric("Average Weekly Sales", f"${kpis['average_weekly_sales']:,.0f}")
metric_columns[2].metric("Stores", f"{kpis['store_count']:,}")
metric_columns[3].metric("Store Weeks", f"{kpis['week_count']:,}")

freshness_columns = st.columns(3)
freshness_columns[0].caption(f"Latest selected sale week: {kpis['latest_sale_date']}")
freshness_columns[1].caption(
    f"Warehouse latest week: {freshness.get('latest_store_week', 'Unavailable')}"
)
freshness_columns[2].caption(
    f"Rows loaded: {freshness.get('forecasting_rows', 0):,} detail / "
    f"{freshness.get('store_weekly_rows', 0):,} store-week"
)

st.divider()

if trend.empty:
    st.info("No sales trend data is available for the selected filters.")
else:
    st.subheader("Sales Trend")
    trend_chart = px.line(
        trend,
        x="sale_date",
        y="weekly_sales",
        markers=True,
        labels={"sale_date": "Week", "weekly_sales": "Sales"},
    )
    st.plotly_chart(trend_chart, use_container_width=True)

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Top Stores")
    if top_stores.empty:
        st.info("No store ranking data is available for the selected filters.")
    else:
        store_chart = px.bar(
            top_stores,
            x="store_id",
            y="total_sales",
            color="region",
            labels={"store_id": "Store", "total_sales": "Sales", "region": "Region"},
        )
        st.plotly_chart(store_chart, use_container_width=True)
        st.dataframe(format_currency(top_stores, "total_sales"), use_container_width=True)

with right_column:
    st.subheader("Top Departments")
    if top_departments.empty:
        st.info("No department ranking data is available for the selected filters.")
    else:
        department_chart = px.bar(
            top_departments,
            x="department",
            y="total_sales",
            labels={"department": "Department", "total_sales": "Sales"},
        )
        st.plotly_chart(department_chart, use_container_width=True)
        st.dataframe(format_currency(top_departments, "total_sales"), use_container_width=True)
