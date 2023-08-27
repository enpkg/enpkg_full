"""Utilities for the unit tests."""

from downloaders import BaseDownloader


def retrieve_zenodo_data():
    """Retrieve the data from Zenodo."""
    downloader = BaseDownloader()
    downloader.download(
        "https://zenodo.org/record/8225411/files/enpkg_taxo_enhancer_output.tar.gz?download=1",
        "tests/data/enpkg_taxo_enhancer_output.tar.gz",
    )