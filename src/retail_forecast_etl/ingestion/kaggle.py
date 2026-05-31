from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Union

from retail_forecast_etl.config import Settings, get_settings
from retail_forecast_etl.utils.logging import get_logger

logger = get_logger(__name__)


class KaggleIngestionError(RuntimeError):
    """Base error for Kaggle ingestion failures."""


class KaggleConfigurationError(KaggleIngestionError):
    """Raised when required Kaggle ingestion configuration is missing or invalid."""


class KaggleDownloadError(KaggleIngestionError):
    """Raised when Kaggle download or file verification fails."""


DatasetDownloader = Callable[[str], Union[str, Path]]


def ingest_kaggle_dataset(
    settings: Settings | None = None,
    *,
    dataset_downloader: DatasetDownloader | None = None,
    force: bool = False,
) -> list[Path]:
    """Download the configured Kaggle dataset into raw storage.

    `kagglehub.dataset_download` downloads to KaggleHub's local cache and returns that path.
    This function then copies the dataset files into this project's raw data directory so
    downstream ETL code and Airflow always use `data/raw`.
    """
    settings = settings or get_settings()
    dataset_slug = _validate_ingestion_settings(settings)
    raw_data_dir = settings.raw_data_dir.expanduser()
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    _configure_kaggle_environment(settings)

    logger.info("Starting Kaggle ingestion for dataset '%s'", dataset_slug)
    logger.info("Raw data destination: %s", raw_data_dir)

    cache_path = _download_with_kagglehub(dataset_slug, dataset_downloader)
    source_files = _dataset_files(cache_path)
    if not source_files:
        raise KaggleDownloadError(
            f"Kaggle dataset '{dataset_slug}' downloaded no usable files into {cache_path}."
        )

    raw_paths = _copy_dataset_files(source_files, cache_path, raw_data_dir, force=force)
    if not raw_paths:
        raise KaggleDownloadError(
            f"Kaggle dataset '{dataset_slug}' produced no raw files in {raw_data_dir}."
        )

    logger.info("Ingestion completed with %s raw file(s)", len(raw_paths))
    _log_file_paths("Raw file", raw_paths)
    return raw_paths


def _validate_ingestion_settings(settings: Settings) -> str:
    dataset_slug = settings.kaggle_dataset_slug.strip()
    if not dataset_slug:
        raise KaggleConfigurationError("KAGGLE_DATASET_SLUG is required for ingestion.")

    if "/" not in dataset_slug or dataset_slug.count("/") != 1:
        raise KaggleConfigurationError(
            "KAGGLE_DATASET_SLUG must use the Kaggle 'owner/dataset-name' format."
        )

    if bool(settings.kaggle_username.strip()) != bool(settings.kaggle_key.strip()):
        raise KaggleConfigurationError(
            "Both KAGGLE_USERNAME and KAGGLE_KEY must be set when using env credentials."
        )

    return dataset_slug


def _configure_kaggle_environment(settings: Settings) -> None:
    kaggle_config_dir = settings.kaggle_config_dir.expanduser()
    os.environ["KAGGLE_CONFIG_DIR"] = str(kaggle_config_dir)
    os.environ["KAGGLEHUB_CACHE"] = str(settings.kagglehub_cache_dir.expanduser())

    if settings.kaggle_username and settings.kaggle_key:
        os.environ["KAGGLE_USERNAME"] = settings.kaggle_username
        os.environ["KAGGLE_KEY"] = settings.kaggle_key


def _download_with_kagglehub(
    dataset_slug: str,
    dataset_downloader: DatasetDownloader | None,
) -> Path:
    if dataset_downloader:
        download_path = dataset_downloader(dataset_slug)
        return Path(download_path).expanduser()

    try:
        import kagglehub
    except ImportError as exc:
        raise KaggleDownloadError(
            "The kagglehub package is not installed. Install dependencies from requirements.txt."
        ) from exc

    try:
        download_path = kagglehub.dataset_download(dataset_slug)
    except Exception as exc:
        raise KaggleDownloadError(
            f"Failed to download Kaggle dataset '{dataset_slug}' with kagglehub. "
            "Check the dataset slug, Kaggle access, credentials if required, and network access."
        ) from exc

    cache_path = Path(download_path).expanduser()
    logger.info("KaggleHub cache path: %s", cache_path)
    return cache_path


def _dataset_files(cache_path: Path) -> list[Path]:
    if cache_path.is_file():
        return [cache_path]

    if not cache_path.is_dir():
        raise KaggleDownloadError(f"KaggleHub returned a path that does not exist: {cache_path}")

    return sorted(path for path in cache_path.rglob("*") if path.is_file() and path.stat().st_size > 0)


def _copy_dataset_files(
    source_files: Iterable[Path],
    cache_path: Path,
    raw_data_dir: Path,
    *,
    force: bool,
) -> list[Path]:
    raw_paths: list[Path] = []

    for source_file in source_files:
        relative_path = source_file.name if cache_path.is_file() else source_file.relative_to(cache_path)
        destination = raw_data_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and destination.stat().st_size > 0 and not force:
            logger.info("Reusing existing raw file: %s", destination)
        else:
            shutil.copy2(source_file, destination)
            logger.info("Copied KaggleHub file %s to %s", source_file, destination)

        raw_paths.append(destination)

    return sorted(raw_paths)


def _existing_non_empty_files(paths: Iterable[Path]) -> list[Path]:
    return sorted(path for path in paths if path.is_file() and path.stat().st_size > 0)


def _log_file_paths(message: str, paths: Iterable[Path]) -> None:
    for path in paths:
        logger.info("%s: %s", message, path)


