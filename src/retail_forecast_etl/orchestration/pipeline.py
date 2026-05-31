from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.ingestion import ingest_kaggle_dataset
from retail_forecast_etl.processing import process_raw_data
from retail_forecast_etl.validation import validate_processed_data
from retail_forecast_etl.warehouse import load_validated_data


def run_pipeline(settings: Settings | None = None) -> None:
    """Run the ETL steps in dependency order once implementations are added."""
    settings = settings or get_settings()
    ingest_kaggle_dataset(settings)
    process_raw_data(settings)
    validate_processed_data(settings)
    load_validated_data(settings)
