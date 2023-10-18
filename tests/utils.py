"""Utilities for the unit tests."""
from glob import glob

from downloaders import BaseDownloader
from downloaders.extractors import AutoExtractor


def retrieve_zenodo_data():
    """Retrieve the data from Zenodo."""
    downloader = BaseDownloader()
    downloader.download(
        "https://zenodo.org/records/10016507/files/dbgi_tropical_mini_toy_dataset.zip?download=1",
        "./data/input/dbgi_tropical_mini_toy_dataset.zip",
    )
    # ALSO EXTRACT ALL OF THE THINGS!
    extractor = AutoExtractor(delete_original_after_extraction=True)
    paths = glob("./data/input/**/*.zip", recursive=True)
    extractor.extract(paths)