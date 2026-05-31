from retail_forecast_etl.config import get_settings
from retail_forecast_etl.utils.logging import configure_logging
from retail_forecast_etl.validation import validate_processed_data


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    validate_processed_data(settings)


if __name__ == "__main__":
    main()
