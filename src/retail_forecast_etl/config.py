from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed project settings shared by ETL, Airflow, and Streamlit."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="local", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    kaggle_dataset_slug: str = Field(default="", alias="KAGGLE_DATASET_SLUG")
    kaggle_username: str = Field(default="", alias="KAGGLE_USERNAME")
    kaggle_key: str = Field(default="", alias="KAGGLE_KEY")
    kaggle_config_dir: Path = Field(default=Path(".kaggle"), alias="KAGGLE_CONFIG_DIR")

    raw_data_dir: Path = Field(default=Path("data/raw"), alias="RAW_DATA_DIR")
    processed_data_dir: Path = Field(default=Path("data/processed"), alias="PROCESSED_DATA_DIR")
    validation_output_dir: Path = Field(
        default=Path("data/validation"),
        alias="VALIDATION_OUTPUT_DIR",
    )

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="retail_sales", alias="POSTGRES_DB")
    postgres_user: str = Field(default="retail_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="retail_password", alias="POSTGRES_PASSWORD")
    postgres_schema: str = Field(default="analytics", alias="POSTGRES_SCHEMA")

    @computed_field
    @property
    def database_url(self) -> str:
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password)
        host = self.postgres_host
        port = self.postgres_port
        database = quote_plus(self.postgres_db)
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
