# Feature Brief: Streamlit Analytics Dashboard

## Goal

Provide a simple dashboard that helps analysts explore sales performance and confirm that warehouse data is useful for analytics.

## Scope

- Connect Streamlit to PostgreSQL.
- Display high-level sales metrics.
- Show trends over time.
- Provide filters for dimensions such as date, store, item, or category when available.
- Support future forecasting outputs without requiring them in the first version.

## Tools

- Streamlit
- PostgreSQL
- SQLAlchemy or psycopg
- pandas
- Plotly or built-in Streamlit charts

## Implementation Notes

- Query analytics-ready tables rather than raw CSVs.
- Cache database reads where appropriate.
- Include a small set of practical views: total sales, sales over time, top products or stores, and data freshness.
- Keep dashboard logic separate from ETL logic.
- Show helpful empty states when data is missing.

## Suggested Build Prompt

```text
Implement a Streamlit dashboard for a retail sales forecasting ETL pipeline. The dashboard should connect to PostgreSQL, query analytics-ready sales tables, and display key metrics such as total sales, sales trends over time, top stores or products, and data freshness. Add filters for available dimensions like date, store, item, or category. Keep the app focused and readable, use cached queries where appropriate, and include clear empty states when warehouse data has not been loaded yet.
```

## Acceptance Criteria

- Dashboard starts locally with Streamlit.
- Dashboard reads from PostgreSQL, not raw files.
- Users can view sales KPIs and trend charts.
- Filters work for available dimensions.
- Missing or empty data is handled gracefully.
