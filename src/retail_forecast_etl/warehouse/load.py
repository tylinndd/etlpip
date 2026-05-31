from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)


def load_validated_data(settings: Settings | None = None) -> None:
    """Placeholder for loading validated datasets into PostgreSQL."""
    settings = settings or get_settings()
    logger.info(
        "Warehouse loading scaffold ready for schema '%s' on database '%s'",
        settings.postgres_schema,
        settings.postgres_db,
    )
    raise NotImplementedError("Warehouse loading will be implemented in the loading feature.")
