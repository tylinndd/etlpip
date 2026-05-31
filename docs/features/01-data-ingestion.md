# Feature Brief: Data Ingestion

## Goal

Download retail sales forecasting datasets from Kaggle and store the original files in a predictable raw data location.

## Scope

- Authenticate with the Kaggle API.
- Download the configured dataset.
- Store raw files locally without mutating their contents.
- Make the ingestion step reusable from both CLI scripts and Airflow tasks.
- Log download status, file names, and destination paths.

## Tools

- Python
- Kaggle API
- pathlib
- logging
- environment variables or `.env`

## Implementation Notes

- Keep Kaggle credentials outside source control.
- Read dataset slug, raw data path, and credential location from configuration.
- Store raw files under a path such as `data/raw/`.
- Make downloads idempotent where possible by checking whether expected files already exist.
- Raise clear exceptions when credentials are missing, the dataset slug is invalid, or no files are downloaded.

## Suggested Build Prompt

```text
Implement the data ingestion feature for a retail sales forecasting ETL pipeline. Use Python and the Kaggle API to download a configured Kaggle dataset into `data/raw/`. Credentials and the dataset slug should come from environment variables or project settings, not hardcoded values. Create reusable functions that can be called by a CLI script or an Airflow task. Include logging, basic error handling, and checks that expected files were downloaded. Do not transform the raw files during ingestion.
```

## Acceptance Criteria

- Running the ingestion step downloads the configured Kaggle dataset.
- Raw files are saved in the expected raw data directory.
- The step can be called from Python without requiring manual interaction.
- Missing credentials produce a clear failure message.
- Logs show which files were downloaded or reused.
