from retail_forecast_etl.ingestion import ingest_kaggle_dataset
from retail_forecast_etl.config import get_settings
from retail_forecast_etl.utils.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    ingest_kaggle_dataset(settings)


if __name__ == "__main__":
    main()
