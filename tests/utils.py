"""Utilities for the unit tests."""
from glob import glob

from downloaders import BaseDownloader
from downloaders.extractors import AutoExtractor


# def retrieve_zenodo_data():
#     """Retrieve the data from Zenodo."""
#     downloader = BaseDownloader()
#     downloader.download("https://zenodo.org/records/10018590/files/enpkg_toy_dataset.zip?download=1","./data/input/enpkg_toy_dataset.zip")
#     # ALSO EXTRACT ALL OF THE THINGS!
#     extractor = AutoExtractor(delete_original_after_extraction=True)
#     paths = glob("./data/input/**/*.zip", recursive=True)
#     extractor.extract(paths)

# Same function, with Zenodo record id as parameter

def retrieve_zenodo_data(record_id, record_name):
    """Retrieve the data from Zenodo.
    Parameters
    ----------
    record_id : str
        The Zenodo record ID.
    record_name : str
        The Zenodo record name.
    """
    downloader = BaseDownloader()
    downloader.download(urls = "https://zenodo.org/records/"+record_id+"/files/"+record_name+"?download=1",
    paths = "./data/input/"+record_name)
    # ALSO EXTRACT ALL OF THE THINGS!
    extractor = AutoExtractor(delete_original_after_extraction=True)
    paths = glob("./data/input/**/*.zip", recursive=True)
    extractor.extract(paths)