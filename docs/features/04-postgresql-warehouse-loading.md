# Feature Brief: PostgreSQL Warehouse Loading

## Goal

Load validated retail sales data into PostgreSQL tables that support analytical SQL queries and dashboarding.

## Scope

- Define database tables for analytics-ready data.
- Connect to PostgreSQL using environment-based configuration.
- Load cleaned datasets into the warehouse.
- Support repeatable local loads.
- Add indexes for common query patterns.

## Tools

- PostgreSQL
- Python
- SQLAlchemy or psycopg
- pandas
- Docker Compose

## Implementation Notes

- Use a clear warehouse schema such as `analytics`.
- Separate raw file storage from database tables.
- Prefer explicit table definitions instead of relying only on implicit dataframe loading.
- Include primary keys or composite uniqueness where appropriate.
- Make load behavior explicit: replace, append, or upsert.
- Add indexes for date, store, item, and category fields if present.

## Suggested Build Prompt

```text
Implement PostgreSQL warehouse loading for a retail sales forecasting ETL pipeline. Define analytics-ready tables, connect using environment variables, and load validated processed datasets into PostgreSQL. Use SQLAlchemy or psycopg with pandas where helpful. Make the load strategy explicit, add useful indexes for common dashboard queries, and ensure the loader can be called from Airflow. Include clear logging and fail fast when the database is unavailable.
```

## Acceptance Criteria

- Validated data loads into PostgreSQL successfully.
- Tables support analytical queries by date, store, item, and sales metrics where available.
- Database connection settings are not hardcoded.
- Load logs show row counts and target tables.
- Failed loads do not silently pass.
