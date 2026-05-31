from pathlib import Path

import pandas as pd

from retail_forecast_etl.config import Settings
from retail_forecast_etl.processing import process_raw_data


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        raw_data_dir=tmp_path / "raw",
        processed_data_dir=tmp_path / "processed",
    )


def write_raw_files(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True)
    (raw_dir / "sales.csv").write_text(
        "\n".join(
            [
                "store_id,department,date,weekly_sales,is_holiday",
                "1,1,2022-01-01,100.00,1",
                "1,1,2022-01-08,120.00,0",
                "1,2,2022-01-01,80.00,1",
                "1,2,2022-01-08,90.00,0",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "features.csv").write_text(
        "\n".join(
            [
                "store_id,date,temperature,fuel_price,markdown_1,markdown_2,markdown_3,markdown_4,markdown_5,cpi,unemployment,is_holiday,holiday_name,season",
                "1,2022-01-01,40.5,3.50,1,2,3,4,5,200.1,4.5,1,New Year,Winter",
                "1,2022-01-08,42.0,3.60,0,0,0,0,0,201.2,4.6,0,None,Winter",
            ]
        ),
        encoding="utf-8",
    )
    (raw_dir / "stores.csv").write_text(
        "\n".join(
            [
                "store_id,store_type,store_size,region",
                "1,A,100000,North",
            ]
        ),
        encoding="utf-8",
    )


def test_process_raw_data_writes_clean_and_feature_outputs(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_raw_files(settings.raw_data_dir)

    output_paths = process_raw_data(settings)

    assert output_paths == [
        settings.processed_data_dir / "sales_clean.csv",
        settings.processed_data_dir / "features_clean.csv",
        settings.processed_data_dir / "stores_clean.csv",
        settings.processed_data_dir / "retail_sales_features.csv",
        settings.processed_data_dir / "store_weekly_sales.csv",
    ]
    assert all(path.is_file() for path in output_paths)

    forecasting = pd.read_csv(settings.processed_data_dir / "retail_sales_features.csv")
    assert len(forecasting) == 4
    assert {
        "sale_date",
        "sales_amount",
        "store_type",
        "markdown_total",
        "year",
        "week_of_year",
        "sales_lag_1_week",
        "sales_rolling_4_week_avg",
    }.issubset(forecasting.columns)

    second_week_department_1 = forecasting[
        (forecasting["department"] == 1) & (forecasting["sale_date"] == "2022-01-08")
    ].iloc[0]
    assert second_week_department_1["sales_lag_1_week"] == 100.0
    assert second_week_department_1["sales_rolling_4_week_avg"] == 100.0

    first_week = forecasting[forecasting["sale_date"] == "2022-01-01"].iloc[0]
    assert first_week["markdown_total"] == 15.0
    assert first_week["holiday_name"] == "New Year"


def test_store_weekly_output_aggregates_departments(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_raw_files(settings.raw_data_dir)

    process_raw_data(settings)

    store_weekly = pd.read_csv(settings.processed_data_dir / "store_weekly_sales.csv")
    assert list(store_weekly["weekly_sales"]) == [180.0, 210.0]
    assert list(store_weekly["department_count"]) == [2, 2]
    assert store_weekly.loc[1, "store_sales_lag_1_week"] == 180.0
