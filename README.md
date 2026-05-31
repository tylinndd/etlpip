# Retail Sales Forecasting ETL Pipeline

Production-style scaffold for a retail sales forecasting ETL pipeline. The project is designed to ingest Kaggle datasets, process and validate them, load analytics-ready tables into PostgreSQL, orchestrate the workflow with Airflow, and serve a Streamlit dashboard.

This repository currently contains the local ETL foundation: KaggleHub ingestion, processing, validation, warehouse loading, Airflow orchestration, and a Streamlit analytics dashboard.

## Product Docs

- [Mini PRD](docs/mini-prd.md)
- [Feature Briefs](docs/features/)

## Architecture

```text
Kaggle API
    -> data/raw
    -> Python processing and feature engineering
    -> data/processed
    -> Pydantic and Great Expectations validation
    -> PostgreSQL analytics schema
    -> Airflow orchestration and Streamlit dashboard
```

## Repository Structure

```text
.
├── dags/                         # Airflow DAG definitions
├── data/
│   ├── raw/                      # Unmodified Kaggle downloads
│   ├── processed/                # Cleaned and feature-ready outputs
│   └── validation/               # Validation reports and artifacts
├── docs/                         # PRD and feature briefs
├── sql/                          # Warehouse schema initialization
├── src/retail_forecast_etl/      # Python package
│   ├── config.py                 # Environment-backed settings
│   ├── ingestion/                # Kaggle ingestion layer
│   ├── processing/               # Cleaning and feature engineering layer
│   ├── validation/               # Pydantic and Great Expectations layer
│   ├── warehouse/                # PostgreSQL connection and loading layer
│   └── orchestration/            # Reusable pipeline entry points
├── streamlit_app/                # Streamlit dashboard app
├── docker-compose.yml            # Local PostgreSQL, Airflow, and Streamlit services
├── Dockerfile                    # Python app image
└── requirements.txt              # Runtime and development dependencies
```

## Setup

1. Create local environment values:

   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your Kaggle dataset slug and credentials.

3. Install the package locally for Python-only development:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

4. Start the local stack:

   ```bash
   docker compose up --build
   ```

Airflow will be available at `http://localhost:8080` and Streamlit at `http://localhost:8501`.

## Configuration

Configuration is loaded from environment variables, with `.env` support through `pydantic-settings`.

Required values for future feature implementations:

- `KAGGLE_DATASET_SLUG`, `KAGGLE_USERNAME`, `KAGGLE_KEY`
- `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, `VALIDATION_OUTPUT_DIR`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SCHEMA`
- `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`

See `.env.example` for defaults suitable for local Docker development.

## Current Entrypoints

- Python package smoke check: `python -m retail_forecast_etl`
- Kaggle ingestion: `python -m retail_forecast_etl.ingestion`
- Process raw CSVs: `python -m retail_forecast_etl.processing`
- Validate processed outputs: `python -m retail_forecast_etl.validation`
- Load warehouse tables: `python -m retail_forecast_etl.warehouse`
- Airflow DAG: `retail_sales_forecasting_etl` in `dags/retail_sales_etl.py`
- Streamlit dashboard: `streamlit run streamlit_app/app.py`

The ingestion step uses `kagglehub.dataset_download()` to download the configured Kaggle dataset, then copies the downloaded files into `data/raw/`, reusing existing raw files when possible. For the default public dataset, Kaggle credentials can be left blank; set `KAGGLE_USERNAME` and `KAGGLE_KEY` if the dataset you configure requires authenticated access. Processing writes analytics-ready CSVs to `data/processed/`. Validation writes JSON reports to `data/validation/` and raises on critical schema or data quality failures so Airflow can stop downstream loading. Warehouse loading uses env-based PostgreSQL config, creates explicit `analytics` tables and indexes, requires successful validation reports, and performs replace-mode loads. The Airflow DAG runs ingestion, processing, validation, and warehouse loading in order with retries, task logs, and failure callbacks. The Streamlit dashboard reads from PostgreSQL warehouse tables and shows KPIs, trends, rankings, filters, data freshness, and empty states.

## Planned Feature Work

- Forecasting model outputs
- Incremental warehouse loading
- CI/CD and deployment automation

## Troubleshooting

- Kaggle failures usually indicate missing `KAGGLE_USERNAME`, `KAGGLE_KEY`, or an invalid `KAGGLE_DATASET_SLUG`.
- Airflow DAG import issues usually indicate the package is not on `PYTHONPATH`; the Docker Compose services mount `src/` and set this automatically.
- PostgreSQL connection failures usually indicate `.env` values do not match the Compose service name, port, or credentials.
- Empty Streamlit views usually indicate PostgreSQL is unavailable or warehouse loading has not run yet.
