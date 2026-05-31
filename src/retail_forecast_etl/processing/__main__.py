from retail_forecast_etl.config import get_settings
from retail_forecast_etl.processing import process_raw_data
from retail_forecast_etl.utils.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    process_raw_data(settings)


if __name__ == "__main__":
    main()
