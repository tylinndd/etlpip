import json
from pathlib import Path

import pytest

from retail_forecast_etl.config import Settings
from retail_forecast_etl.validation import DataValidationError, validate_processed_data


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        processed_data_dir=tmp_path / "processed",
        validation_output_dir=tmp_path / "validation",
    )


def write_valid_processed_files(processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True)
    (processed_dir / "retail_sales_features.csv").write_text(
        "\n".join(
            [
                "store_id,department,sale_date,weekly_sales,sales_amount,store_type,store_size,region,temperature,fuel_price,markdown_total,cpi,unemployment,is_holiday,holiday_name,season,year,quarter,month,week_of_year,day_of_week,sales_lag_1_week,sales_lag_4_weeks,sales_rolling_4_week_avg,sales_rolling_12_week_avg",
                "1,1,2022-01-01,100.0,100.0,A,100000,North,40.5,3.5,15.0,200.1,4.5,True,New Year,Winter,2022,1,1,52,5,,,,",
                "1,1,2022-01-08,120.0,120.0,A,100000,North,42.0,3.6,0.0,201.2,4.6,False,None,Winter,2022,1,1,1,5,100.0,,100.0,100.0",
            ]
        ),
        encoding="utf-8",
    )
    (processed_dir / "store_weekly_sales.csv").write_text(
        "\n".join(
            [
                "store_id,sale_date,weekly_sales,department_count,is_holiday,markdown_total,store_type,store_size,region,holiday_name,season,sales_amount,year,quarter,month,week_of_year,day_of_week,store_sales_lag_1_week,store_sales_rolling_4_week_avg",
                "1,2022-01-01,100.0,1,True,15.0,A,100000,North,New Year,Winter,100.0,2022,1,1,52,5,,",
                "1,2022-01-08,120.0,1,False,0.0,A,100000,North,None,Winter,120.0,2022,1,1,1,5,100.0,100.0",
            ]
        ),
        encoding="utf-8",
    )


def test_validate_processed_data_writes_reports(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_valid_processed_files(settings.processed_data_dir)

    report_paths = validate_processed_data(settings)

    assert report_paths == [
        settings.validation_output_dir / "retail_sales_features_validation_report.json",
        settings.validation_output_dir / "store_weekly_sales_validation_report.json",
    ]
    assert all(path.is_file() for path in report_paths)
    report = json.loads(report_paths[0].read_text(encoding="utf-8"))
    assert report["pydantic"]["success"] is True
    assert report["great_expectations"]["success"] is True


def test_validate_processed_data_fails_on_duplicate_key(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    write_valid_processed_files(settings.processed_data_dir)
    sales_path = settings.processed_data_dir / "retail_sales_features.csv"
    original = sales_path.read_text(encoding="utf-8")
    duplicate_row = original.splitlines()[1]
    sales_path.write_text(f"{original}\n{duplicate_row}", encoding="utf-8")

    with pytest.raises(DataValidationError, match="Critical data quality checks failed"):
        validate_processed_data(settings)
