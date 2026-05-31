from sqlalchemy import create_engine, text

from streamlit_app.dashboard_data import (
    DashboardFilters,
    fetch_data_freshness,
    fetch_date_bounds,
    fetch_filter_options,
    fetch_kpis,
    fetch_sales_trend,
    fetch_top_departments,
    fetch_top_stores,
)


def create_dashboard_test_engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE store_weekly_sales (
                    store_id INTEGER,
                    sale_date DATE,
                    weekly_sales NUMERIC,
                    department_count INTEGER,
                    is_holiday BOOLEAN,
                    markdown_total NUMERIC,
                    temperature NUMERIC,
                    fuel_price NUMERIC,
                    cpi NUMERIC,
                    unemployment NUMERIC,
                    store_type TEXT,
                    store_size INTEGER,
                    region TEXT,
                    holiday_name TEXT,
                    season TEXT,
                    sales_amount NUMERIC,
                    year INTEGER,
                    quarter INTEGER,
                    month INTEGER,
                    week_of_year INTEGER,
                    day_of_week INTEGER,
                    is_month_start BOOLEAN,
                    is_month_end BOOLEAN,
                    store_sales_lag_1_week NUMERIC,
                    store_sales_rolling_4_week_avg NUMERIC
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE retail_sales_features (
                    store_id INTEGER,
                    department INTEGER,
                    sale_date DATE,
                    weekly_sales NUMERIC,
                    sales_amount NUMERIC,
                    store_type TEXT,
                    store_size INTEGER,
                    region TEXT
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO store_weekly_sales
                (store_id, sale_date, weekly_sales, department_count, is_holiday,
                 markdown_total, temperature, fuel_price, cpi, unemployment,
                 store_type, store_size, region, holiday_name, season, sales_amount,
                 year, quarter, month, week_of_year, day_of_week, is_month_start,
                 is_month_end, store_sales_lag_1_week, store_sales_rolling_4_week_avg)
                VALUES
                (1, '2022-01-01', 100.0, 2, 1, 10.0, 40.0, 3.5, 200.0, 4.5,
                 'A', 100000, 'North', 'New Year', 'Winter', 100.0,
                 2022, 1, 1, 52, 5, 1, 0, NULL, NULL),
                (2, '2022-01-01', 250.0, 2, 1, 5.0, 42.0, 3.6, 201.0, 4.6,
                 'B', 120000, 'South', 'New Year', 'Winter', 250.0,
                 2022, 1, 1, 52, 5, 1, 0, NULL, NULL),
                (1, '2022-01-08', 150.0, 2, 0, 0.0, 43.0, 3.7, 202.0, 4.7,
                 'A', 100000, 'North', 'None', 'Winter', 150.0,
                 2022, 1, 1, 1, 5, 0, 0, 100.0, 100.0)
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO retail_sales_features
                (store_id, department, sale_date, weekly_sales, sales_amount,
                 store_type, store_size, region)
                VALUES
                (1, 1, '2022-01-01', 60.0, 60.0, 'A', 100000, 'North'),
                (1, 2, '2022-01-01', 40.0, 40.0, 'A', 100000, 'North'),
                (2, 1, '2022-01-01', 250.0, 250.0, 'B', 120000, 'South'),
                (1, 1, '2022-01-08', 90.0, 90.0, 'A', 100000, 'North'),
                (1, 2, '2022-01-08', 60.0, 60.0, 'A', 100000, 'North')
                """
            )
        )
    return engine


def test_dashboard_queries_return_kpis_and_filter_options() -> None:
    engine = create_dashboard_test_engine()

    min_date, max_date = fetch_date_bounds(engine, None)
    options = fetch_filter_options(engine, None)
    kpis = fetch_kpis(engine, None, DashboardFilters())

    assert str(min_date) == "2022-01-01"
    assert str(max_date) == "2022-01-08"
    assert options == {
        "store_ids": [1, 2],
        "regions": ["North", "South"],
        "departments": [1, 2],
    }
    assert kpis["total_sales"] == 500.0
    assert kpis["store_count"] == 2
    assert kpis["week_count"] == 3


def test_dashboard_queries_apply_filters() -> None:
    engine = create_dashboard_test_engine()
    filters = DashboardFilters(store_ids=(1,), regions=("North",), departments=(2,))

    kpis = fetch_kpis(engine, None, filters)
    trend = fetch_sales_trend(engine, None, filters)
    top_stores = fetch_top_stores(engine, None, filters)
    top_departments = fetch_top_departments(engine, None, filters)
    freshness = fetch_data_freshness(engine, None)

    assert kpis["total_sales"] == 100.0
    assert kpis["store_count"] == 1
    assert kpis["week_count"] == 2
    assert list(trend["weekly_sales"]) == [40.0, 60.0]
    assert top_stores.iloc[0]["store_id"] == 1
    assert top_stores.iloc[0]["total_sales"] == 100.0
    assert top_departments.iloc[0]["department"] == 2
    assert top_departments.iloc[0]["total_sales"] == 100.0
    assert freshness["store_weekly_rows"] == 3
    assert freshness["forecasting_rows"] == 5
