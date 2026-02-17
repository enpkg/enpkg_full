"""
Database downloader & loader for the different enrichers. 
"""

from typing import NamedTuple
from pathlib import Path
import pickle
from logging import Logger
from time import time

import pandas as pd
from matchms import Spectrum
from downloaders import BaseDownloader

from enpkg.monolith.configuration.isdb_configuration_class import ISDBEnricherConfig
from enpkg.monolith.exceptions import DBLoaderError

# Valid URL field names that can be used in redownload_if_exists
VALID_URL_FIELDS: list[str] = [
    "taxo_db_metadata",
    "spectral_db_pos",
    "spectral_db_neg",
    "taxo_db_pathways",
    "taxo_db_superclasses",
    "taxo_db_classes",
]


class DownloadInfo(NamedTuple):
    """Container for database download information."""
    field_name: str
    url: str
    local_path: str


class DBLoader:
    """
    Loader for the different databases (ISDB, Taxonomical, etc).
    """

    def __init__(self, configuration: ISDBEnricherConfig, logger: Logger):

        self.configuration = configuration
        self.logger = logger
        self.downloads: list[DownloadInfo] = []

        if self.configuration.urls is not None:
            self._validate_redownload_fields()
            self._collect_downloads()
            if self.downloads:
                self._download_databases()

    def _validate_redownload_fields(self) -> None:
        """Validate that redownload_if_exists contains only valid URL field names."""
        
        redownload = self.configuration.general_params.redownload_if_exists
        
        # If it's a boolean, no validation needed
        if isinstance(redownload, bool):
            return
        
        # If it's a list, validate each field name
        if isinstance(redownload, list):
            invalid_fields = [field for field in redownload if field not in VALID_URL_FIELDS]
            if invalid_fields:
                raise DBLoaderError(
                    f"Invalid field name(s): {invalid_fields}. "
                    f"Valid fields are: {VALID_URL_FIELDS}"
                )

    def _collect_downloads(self) -> None:
        """Match URLs to their corresponding local paths by field name."""
        
        for field_name, url in self.configuration.urls.items():
            local_path = getattr(self.configuration.paths, field_name, None)
            if local_path is not None:
                self.downloads.append(DownloadInfo(field_name, url, local_path))
            else:
                self.logger.warning(
                    f"No local path defined for URL '{field_name}'; skipping download"
                )

    def _download_databases(self) -> None:
        """Download databases from URLs to local paths."""

        self.logger.info(f"Downloading {len(self.downloads)} databases")
        downloader = BaseDownloader()
        for download in self.downloads:
            try:
                p = Path(download.local_path)
                redownload = self.configuration.general_params.redownload_if_exists
                should_redownload = (
                    redownload is True or 
                    (isinstance(redownload, list) and download.field_name in redownload)
                )
                
                if p.is_file() and not should_redownload:
                    self.logger.info(
                        f"Database at {download.local_path} already exists; skipping download"
                    )
                else:
                    downloader.download(download.url, download.local_path)
                    self.logger.info(f"Downloaded database from {download.url} to {download.local_path}")
                    
            except Exception as e:
                self.logger.error(
                    f"Failed to download database from {download.url} to {download.local_path}: {str(e)}"
                )
        self.logger.info("Databases downloaded successfully")

    def load_taxonomical_databases(self) -> None:
        """Load databases into memory."""

        self.logger.info("Loading databases into memory")
        
        start = time()
        self.lotus_metadata: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_metadata, low_memory=False
        )
        self.logger.info(f"Loaded Taxonomical Database metadata in {time() - start:.2f} seconds")
        self.logger.debug(f"Loaded Taxonomical Database metadata with columns: {self.lotus_metadata.columns.tolist()}")
        
        start = time()
        self.lotus_metadata_pathways: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_pathways,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database pathways in {time() - start:.2f} seconds")
        self._number_of_pathways = self.lotus_metadata_pathways.shape[1]
        self._pathways = self.lotus_metadata_pathways.columns
        
        start = time()
        self.lotus_metadata_superclasses: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_superclasses,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database superclasses in {time() - start:.2f} seconds")
        self._number_of_superclasses = self.lotus_metadata_superclasses.shape[1]
        self._superclasses = self.lotus_metadata_superclasses.columns
        
        start = time()
        self.lotus_metadata_classes: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_classes,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database classes in {time() - start:.2f} seconds")
        self._number_of_classes = self.lotus_metadata_classes.shape[1]
        self._classes = self.lotus_metadata_classes.columns
        
        self.logger.info(
            "Loaded %d Taxonomical Database metadata entries",
            len(self.lotus_metadata),
        )

    def load_spectral_databases(self, mode) -> None:
        """Load spectral databases into memory."""
        start = time()
        if mode == "pos":
            with open(self.configuration.paths.spectral_db_pos, "rb") as f:
                self.spectral_db: list[Spectrum] = pickle.load(f)
        elif mode == "neg":
            with open(self.configuration.paths.spectral_db_neg, "rb") as f:
                self.spectral_db: list[Spectrum] = pickle.load(f)
        else:
            raise ValueError(f"Invalid mode '{mode}' for loading spectral database")
        self.logger.debug(f"Loaded {mode} mode spectral database in {time() - start:.2f} seconds")
