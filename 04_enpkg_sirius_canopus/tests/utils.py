"""Utilities for the unit tests."""

from downloaders import BaseDownloader


def retrieve_zenodo_data():
    """Retrieve the data from Zenodo."""
    downloader = BaseDownloader()
    downloader.download(
        "https://zenodo.org/record/8232472/files/enpkg_mn_isdb_taxo_output.tar.gz?download=1",
        "tests/data/enpkg_mn_isdb_taxo_output.tar.gz",
    )