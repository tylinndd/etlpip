# Feature Brief: Airflow Orchestration

## Goal

Use Apache Airflow to schedule and monitor the complete ETL workflow from ingestion through warehouse loading.

## Scope

- Create an Airflow DAG for the ETL pipeline.
- Define tasks for extract, transform, validate, and load steps.
- Configure task dependencies.
- Capture execution logs and failures.
- Support manual and scheduled runs.

## Tools

- Apache Airflow
- PythonOperator or TaskFlow API
- Docker Compose
- Python logging

## Implementation Notes

- Keep business logic in reusable Python modules, not directly inside the DAG file.
- Use Airflow for orchestration only.
- Make dependencies explicit: ingest, process, validate, load, then optional dashboard refresh signal.
- Set sensible retries and retry delays.
- Use environment variables or Airflow connections for credentials.

## Suggested Build Prompt

```text
Implement Apache Airflow orchestration for a retail sales forecasting ETL pipeline. Create a DAG that runs ingestion, processing, validation, and PostgreSQL loading in the correct order. Keep ETL logic in reusable Python modules and call those modules from Airflow tasks. Configure logging, retries, scheduling, and failure behavior so a validation or loading failure stops downstream tasks. The DAG should work in the project's Dockerized local environment.
```

## Acceptance Criteria

- Airflow shows a DAG for the retail sales ETL pipeline.
- The DAG runs all ETL tasks in the correct order.
- Failed validation prevents database loading.
- Task logs are visible in Airflow.
- The DAG can run manually and on a configured schedule.
