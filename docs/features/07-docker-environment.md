# Feature Brief: Dockerized Local Environment

## Goal

Provide a reproducible local environment for running PostgreSQL, Airflow, Streamlit, and the ETL code.

## Scope

- Define Docker services for the project.
- Configure PostgreSQL.
- Configure Airflow.
- Configure Streamlit.
- Mount project code and data directories where needed.
- Document required environment variables.

## Tools

- Docker
- Docker Compose
- PostgreSQL image
- Airflow image
- Python image or project-specific app image
- `.env`

## Implementation Notes

- Use Docker Compose for local development.
- Keep secrets and credentials in `.env`, not in committed files.
- Provide named volumes for PostgreSQL and Airflow metadata if needed.
- Expose sensible local ports for Airflow, PostgreSQL, and Streamlit.
- Make startup order and health checks clear.

## Suggested Build Prompt

```text
Create a Dockerized local development environment for a retail sales forecasting ETL pipeline. Use Docker Compose to run PostgreSQL, Airflow, and Streamlit along with the Python ETL code. Configure environment variables through a `.env` file, use volumes for persistent database state where appropriate, expose local ports, and document startup commands. The environment should support running the Airflow DAG and the Streamlit dashboard against the same PostgreSQL warehouse.
```

## Acceptance Criteria

- `docker compose up` starts the required services.
- PostgreSQL is reachable by ETL code, Airflow, and Streamlit.
- Airflow can discover and run the pipeline DAG.
- Streamlit can connect to the warehouse.
- Required environment variables are documented.
