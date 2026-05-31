from retail_forecast_etl.config import get_settings
from retail_forecast_etl.utils.logging import configure_logging
from retail_forecast_etl.warehouse import load_validated_data


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    load_validated_data(settings)


if __name__ == "__main__":
    main()
