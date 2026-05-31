from pathlib import Path

from retail_forecast_etl.orchestration import airflow_tasks


def test_airflow_task_wrappers_return_serializable_results(monkeypatch) -> None:
    monkeypatch.setattr(airflow_tasks, "ingest_kaggle_dataset", lambda settings: [Path("raw.csv")])
    monkeypatch.setattr(
        airflow_tasks,
        "process_raw_data",
        lambda settings: [Path("processed.csv")],
    )
    monkeypatch.setattr(
        airflow_tasks,
        "validate_processed_data",
        lambda settings: [Path("report.json")],
    )
    monkeypatch.setattr(
        airflow_tasks,
        "load_validated_data",
        lambda settings: {"retail_sales_features": 1},
    )

    assert airflow_tasks.run_ingestion_task() == ["raw.csv"]
    assert airflow_tasks.run_processing_task() == ["processed.csv"]
    assert airflow_tasks.run_validation_task() == ["report.json"]
    assert airflow_tasks.run_warehouse_load_task() == {"retail_sales_features": 1}


def test_airflow_dag_declares_expected_tasks_and_dependencies() -> None:
    dag_source = Path("dags/retail_sales_etl.py").read_text(encoding="utf-8")

    assert 'DAG_ID = "retail_sales_forecasting_etl"' in dag_source
    assert 'task_id="ingest_kaggle_dataset"' in dag_source
    assert 'task_id="process_raw_data"' in dag_source
    assert 'task_id="validate_processed_data"' in dag_source
    assert 'task_id="load_postgresql_warehouse"' in dag_source
    assert "ingest() >> process() >> validate() >> load()" in dag_source
    assert '"retries": 2' in dag_source
    assert "on_failure_callback" in dag_source
    assert "max_active_runs=1" in dag_source
