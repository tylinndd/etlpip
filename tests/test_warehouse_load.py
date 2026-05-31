import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from retail_forecast_etl.config import Settings
from retail_forecast_etl.warehouse import WarehouseLoadError, load_validated_data


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        processed_data_dir=tmp_path / "processed",
        validation_output_dir=tmp_path / "validation",
        postgres_schema="",
    )


def write_processed_files(processed_dir: Path, weekly_sales: str = "100.0") -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "retail_sales_features.csv").write_text(
        "\n".join(
            [
                "store_id,department,sale_date,weekly_sales,sales_amount,store_type,store_size,region,temperature,fuel_price,markdown_1,markdown_2,markdown_3,markdown_4,markdown_5,markdown_total,cpi,unemployment,is_holiday,holiday_name,season,year,quarter,month,week_of_year,day_of_week,is_month_start,is_month_end,sales_lag_1_week,sales_lag_4_weeks,sales_rolling_4_week_avg,sales_rolling_12_week_avg,store_department_sales_rank",
                f"1,1,2022-01-01,{weekly_sales},{weekly_sales},A,100000,North,40.5,3.5,1,2,3,4,5,15.0,200.1,4.5,True,New Year,Winter,2022,1,1,52,5,True,False,,,,,1.0",
            ]
        ),
        encoding="utf-8",
    )
    (processed_dir / "store_weekly_sales.csv").write_text(
        "\n".join(
            [
                "store_id,sale_date,weekly_sales,department_count,is_holiday,markdown_total,temperature,fuel_price,cpi,unemployment,store_type,store_size,region,holiday_name,season,sales_amount,year,quarter,month,week_of_year,day_of_week,is_month_start,is_month_end,store_sales_lag_1_week,store_sales_rolling_4_week_avg",
                f"1,2022-01-01,{weekly_sales},1,True,15.0,40.5,3.5,200.1,4.5,A,100000,North,New Year,Winter,{weekly_sales},2022,1,1,52,5,True,False,,",
            ]
        ),
        encoding="utf-8",
    )


def write_successful_validation_reports(validation_dir: Path) -> None:
    validation_dir.mkdir(parents=True)
    report = {
        "pydantic": {"success": True},
        "great_expectations": {"success": True},
    }
    for name in [
        "retail_sales_features_validation_report.json",
        "store_weekly_sales_validation_report.json",
    ]:
        (validation_dir / name).write_text(json.dumps(report), encoding="utf-8")


def test_load_validated_data_replaces_rows(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_processed_files(settings.processed_data_dir, weekly_sales="100.0")
    write_successful_validation_reports(settings.validation_output_dir)
    engine = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}", future=True)

    first_counts = load_validated_data(settings, engine=engine, chunk_size=1)
    assert first_counts == {"retail_sales_features": 1, "store_weekly_sales": 1}

    write_processed_files(settings.processed_data_dir, weekly_sales="250.0")
    second_counts = load_validated_data(settings, engine=engine, chunk_size=1)
    assert second_counts == {"retail_sales_features": 1, "store_weekly_sales": 1}

    with engine.connect() as connection:
        sales_amount = connection.execute(
            text("SELECT weekly_sales FROM retail_sales_features")
        ).scalar_one()
        row_count = connection.execute(text("SELECT COUNT(*) FROM retail_sales_features")).scalar_one()

    assert float(sales_amount) == 250.0
    assert row_count == 1


def test_load_validated_data_requires_successful_validation_reports(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_processed_files(settings.processed_data_dir)
    engine = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}", future=True)

    with pytest.raises(WarehouseLoadError, match="Validation report"):
        load_validated_data(settings, engine=engine)
