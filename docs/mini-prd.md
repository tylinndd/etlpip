# Mini PRD: Retail Sales Forecasting ETL Pipeline

## Project Summary

Build a production-style ETL pipeline that ingests retail sales forecasting datasets from Kaggle, cleans and validates the data, stores analytics-ready tables in PostgreSQL, and supports dashboarding plus future forecasting workflows.

## Problem

Retail forecasting datasets often arrive as disconnected CSV files. Before analysts or forecasting models can use them, the data needs to be downloaded, cleaned, normalized, merged, validated, and loaded into a queryable warehouse. This project simulates the type of automated workflow an enterprise data engineering team would build for retail analytics.

## Goals

- Automate ingestion of Kaggle datasets.
- Build scalable, repeatable ETL workflows.
- Validate data quality before loading data into the warehouse.
- Store cleaned data in PostgreSQL.
- Create analytics-ready datasets for dashboards and forecasting.
- Orchestrate the full workflow with Apache Airflow.
- Provide clear architecture and workflow documentation.

## Non-Goals

- Real-time streaming ingestion.
- Multi-region cloud deployment.
- Large-scale distributed processing.
- Production ML forecasting model training.
- Full CI/CD pipeline in the first version.
- Data lake implementation in the first version.

## Primary User

Data engineers and analysts who need to review retail sales performance, prepare forecasting datasets, and understand the reliability of the underlying data pipeline.

## Scope

### In Scope

- Kaggle API-based dataset download.
- Local raw data storage.
- Python-based data cleaning and transformation.
- Feature generation for forecasting workflows.
- Schema validation with Pydantic.
- Data quality checks with Great Expectations.
- PostgreSQL warehouse loading.
- Airflow DAG orchestration.
- Docker-based reproducible local environment.
- Streamlit dashboard for analytics views.

### Out of Scope

- Streaming architecture.
- Cloud-managed infrastructure.
- Distributed processing with Spark or similar tools.
- Production-grade user authentication.
- Automated model retraining.
- Enterprise monitoring stack.

## Tools and Technology

| Category | Tool |
| --- | --- |
| Language | Python |
| Data Source | Kaggle API |
| Data Processing | pandas |
| Validation | Pydantic, Great Expectations |
| Database | PostgreSQL |
| Orchestration | Apache Airflow |
| Containerization | Docker, Docker Compose |
| Dashboard | Streamlit |
| Configuration | Environment variables, `.env` file |

## System Architecture

```text
Kaggle API
    |
    v
Extract Layer
    |
    v
Raw Local Storage
    |
    v
Transform Layer
    |
    v
Validation Layer
    |
    v
PostgreSQL Warehouse
    |
    v
Dashboard / Forecasting Workflows
```

## Core Features

- [Data Ingestion](features/01-data-ingestion.md)
- [Data Processing and Feature Engineering](features/02-data-processing-and-feature-engineering.md)
- [Data Validation](features/03-data-validation.md)
- [PostgreSQL Warehouse Loading](features/04-postgresql-warehouse-loading.md)
- [Airflow Orchestration](features/05-airflow-orchestration.md)
- [Streamlit Analytics Dashboard](features/06-streamlit-dashboard.md)
- [Dockerized Local Environment](features/07-docker-environment.md)
- [Project Documentation](features/08-project-documentation.md)

## Success Criteria

- ETL pipeline can run from raw Kaggle download through PostgreSQL loading.
- Airflow can orchestrate the pipeline successfully.
- Cleaned tables are available for analytical SQL queries.
- Validation checks run automatically and fail the pipeline when critical data quality issues appear.
- Docker environment is reproducible for local development.
- Streamlit dashboard can read from PostgreSQL and display useful sales analytics.
- Repository includes clear setup, architecture, and workflow documentation.

## Future Enhancements

- Cloud deployment.
- Incremental loading.
- Real-time ingestion.
- ML forecasting pipeline.
- CI/CD integration.
- Data lake integration.
