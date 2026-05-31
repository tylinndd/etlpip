from retail_forecast_etl.config import Settings, get_settings


def build_database_url(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return str(settings.database_url)
