"""Get cleaned GNPS spectral data from Zenodo."""

from downloaders import BaseDownloader
import pandas as pd

import os
import numpy as np
from matchms.importing import load_from_mgf


GNPS_CLEANED_SPECTRA_URL = (
    "https://zenodo.org/records/11566051/files/cleaned_gnps_library.mgf?download=1"
)
path_data = os.path.join(
    os.path.dirname(os.getcwd()), "enpkg_full/monolith/downloads/"
)  # "..." enter your pathname to the downloaded file
file_mgf = os.path.join(path_data, "cleaned_gnps_library.mgf")


def gnps_spectral_fetcher() -> None:
    """Download the GNPS spectral data and save it in the data_loc folder."""
    downloader = BaseDownloader()
    downloader.download(
        GNPS_CLEANED_SPECTRA_URL, "monolith/downloads/cleaned_gnps_library.mgf"
    )


def load_mgf(file_mgf) -> None:
    """Load the GNPS spectral data from the MGF file."""
    spectrums = list(load_from_mgf(file_mgf))
    print(f"{len(spectrums)} spectrums found and imported")
    return spectrums


def return_inchikeys(spectrums):
    inchikeys = []
    inchikeys = [s.get("inchikey") for s in spectrums]
    found_inchikeys = np.sum([1 for x in inchikeys if x is not None])
    print(f"Found {int(found_inchikeys)} inchikeys in metadata")


if __name__ == "__main__":
    # gnps_spectral_fetcher()
    spectrums = load_mgf(file_mgf)
    return_inchikeys(spectrums)
