from pathlib import Path

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)


def validate_processed_data(settings: Settings | None = None) -> list[Path]:
    """Placeholder for Pydantic and Great Expectations validation checks."""
    settings = settings or get_settings()
    logger.info(
        "Validation scaffold ready for processed data in %s with reports in %s",
        settings.processed_data_dir,
        settings.validation_output_dir,
    )
    raise NotImplementedError("Validation will be implemented in the validation feature.")
