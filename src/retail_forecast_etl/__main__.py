from retail_forecast_etl.config import get_settings
from retail_forecast_etl.utils.logging import configure_logging, get_logger


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("Retail forecasting ETL scaffold is configured for %s", settings.environment)


if __name__ == "__main__":
    main()
