from pathlib import Path

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)


def process_raw_data(settings: Settings | None = None) -> list[Path]:
    """Placeholder for cleaning raw CSV files and creating processed datasets."""
    settings = settings or get_settings()
    logger.info(
        "Processing scaffold ready for raw data in %s and outputs in %s",
        settings.raw_data_dir,
        settings.processed_data_dir,
    )
    raise NotImplementedError("Processing will be implemented in the processing feature.")
