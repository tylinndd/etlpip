import streamlit as st

from retail_forecast_etl.config import get_settings


st.set_page_config(page_title="Retail Sales Forecasting", layout="wide")

settings = get_settings()

st.title("Retail Sales Forecasting")
st.caption("Dashboard scaffold for PostgreSQL-backed retail analytics.")

st.info(
    "Warehouse queries and charts will be added with the Streamlit dashboard feature. "
    "This placeholder confirms that configuration can be loaded."
)

with st.expander("Current warehouse configuration"):
    st.write(
        {
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db,
            "schema": settings.postgres_schema,
        }
    )
