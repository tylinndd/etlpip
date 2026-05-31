# Feature Brief: Data Validation

## Goal

Validate processed data before it is loaded into PostgreSQL so unreliable data does not reach the analytics layer.

## Scope

- Enforce expected schemas.
- Validate data types and required fields.
- Run data quality checks for nulls, duplicates, ranges, and accepted values.
- Produce validation reports or logs.
- Stop downstream loading when critical checks fail.

## Tools

- Python
- Pydantic
- Great Expectations
- logging

## Implementation Notes

- Use Pydantic for row-level or configuration-level schema models.
- Use Great Expectations for dataset-level checks.
- Validate critical fields such as dates, sales amounts, store IDs, item IDs, and other required dimensions.
- Separate warnings from blocking failures.
- Make the validation step callable from Airflow.

## Suggested Build Prompt

```text
Implement a data validation layer for a retail sales forecasting ETL pipeline. Use Pydantic for explicit schema models and Great Expectations for dataset-level quality checks. Validate required columns, data types, non-null fields, duplicate records, date ranges, and numeric sales ranges. The validation step should produce useful logs or reports and should raise an error when critical expectations fail so Airflow can stop the pipeline before loading bad data into PostgreSQL.
```

## Acceptance Criteria

- Processed datasets are checked before database loading.
- Critical schema mismatches fail the pipeline.
- Great Expectations checks cover nulls, uniqueness, valid ranges, and required columns.
- Validation output is easy to inspect.
- The validation code can be run locally and from Airflow.
