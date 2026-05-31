from pathlib import Path

import pytest

from retail_forecast_etl.config import Settings
from retail_forecast_etl.ingestion import (
    KaggleConfigurationError,
    ingest_kaggle_dataset,
)


def make_settings(tmp_path: Path, *, username: str = "", key: str = "") -> Settings:
    return Settings(
        kaggle_dataset_slug="owner/dataset",
        kaggle_username=username,
        kaggle_key=key,
        kaggle_config_dir=tmp_path / ".kaggle",
        raw_data_dir=tmp_path / "raw",
    )


def test_missing_dataset_slug_raises_clear_error(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    settings.kaggle_dataset_slug = ""

    with pytest.raises(KaggleConfigurationError, match="KAGGLE_DATASET_SLUG"):
        ingest_kaggle_dataset(settings, dataset_downloader=lambda dataset: tmp_path)


def test_partial_credentials_raise_clear_error(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, username="user", key="")

    with pytest.raises(KaggleConfigurationError, match="Both KAGGLE_USERNAME and KAGGLE_KEY"):
        ingest_kaggle_dataset(settings, dataset_downloader=lambda dataset: tmp_path)


def test_copies_kagglehub_downloaded_files_to_raw_dir(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    cache_dir = tmp_path / "kagglehub-cache"
    (cache_dir / "sales.csv").parent.mkdir(parents=True)
    (cache_dir / "sales.csv").write_text("raw sales", encoding="utf-8")
    (cache_dir / "nested" / "stores.csv").parent.mkdir(parents=True)
    (cache_dir / "nested" / "stores.csv").write_text("raw stores", encoding="utf-8")

    paths = ingest_kaggle_dataset(settings, dataset_downloader=lambda dataset: cache_dir)

    assert paths == [
        settings.raw_data_dir / "nested" / "stores.csv",
        settings.raw_data_dir / "sales.csv",
    ]
    assert (settings.raw_data_dir / "sales.csv").read_text(encoding="utf-8") == "raw sales"
    assert (settings.raw_data_dir / "nested" / "stores.csv").read_text(encoding="utf-8") == "raw stores"


def test_reuses_existing_raw_files_without_force(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    cache_dir = tmp_path / "kagglehub-cache"
    cache_file = cache_dir / "sales.csv"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("new raw data", encoding="utf-8")
    raw_file = settings.raw_data_dir / "sales.csv"
    raw_file.parent.mkdir(parents=True)
    raw_file.write_text("existing raw data", encoding="utf-8")

    paths = ingest_kaggle_dataset(settings, dataset_downloader=lambda dataset: cache_dir)

    assert paths == [raw_file]
    assert raw_file.read_text(encoding="utf-8") == "existing raw data"


def test_force_refreshes_existing_raw_files(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    cache_dir = tmp_path / "kagglehub-cache"
    cache_file = cache_dir / "sales.csv"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("new raw data", encoding="utf-8")
    raw_file = settings.raw_data_dir / "sales.csv"
    raw_file.parent.mkdir(parents=True)
    raw_file.write_text("existing raw data", encoding="utf-8")

    paths = ingest_kaggle_dataset(settings, dataset_downloader=lambda dataset: cache_dir, force=True)

    assert paths == [raw_file]
    assert raw_file.read_text(encoding="utf-8") == "new raw data"
