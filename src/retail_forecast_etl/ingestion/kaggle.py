from pathlib import Path

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)


def ingest_kaggle_dataset(settings: Settings | None = None) -> list[Path]:
    """Placeholder for downloading the configured Kaggle dataset into raw storage."""
    settings = settings or get_settings()
    logger.info(
        "Kaggle ingestion scaffold ready for dataset '%s' into %s",
        settings.kaggle_dataset_slug or "<unset>",
        settings.raw_data_dir,
    )
    raise NotImplementedError("Kaggle ingestion will be implemented in the ingestion feature.")
