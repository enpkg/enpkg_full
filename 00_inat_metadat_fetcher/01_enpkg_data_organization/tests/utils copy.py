"""Utilities for the unit tests."""
from glob import glob

from downloaders import BaseDownloader
from downloaders.extractors import AutoExtractor


def retrieve_zenodo_data():
    """Retrieve the data from Zenodo."""
    downloader = BaseDownloader()
    downloader.download(
        "https://zenodo.org/record/8152039/files/dbgkg_tropical_toydataset.tar.gz?download=1",
        "tests/data/dbgkg_tropical_toydataset.tar.gz",
    )
    # ALSO EXTRACT ALL OF THE THINGS!
    extractor = AutoExtractor(delete_original_after_extraction=True)
    paths = glob("tests/data/**/*.gz", recursive=True)
    extractor.extract(paths)