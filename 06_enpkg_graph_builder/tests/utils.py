"""Utilities for the unit tests."""

from downloaders import BaseDownloader


def retrieve_zenodo_data():
    """Retrieve the data from Zenodo."""
    downloader = BaseDownloader()
    downloader.download(
        "https://zenodo.org/record/8252033/files/enpkg_meta_analysis_output.tar.gz?download=1",
        "tests/data/enpkg_meta_analysis_output.tar.gz",
    )