import os
import logging
from tqdm import tqdm
from typing import Dict, Set
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import pandas as pd
from matchms.importing import load_from_mgf
from matchms.exporting import save_as_mgf
from downloaders import BaseDownloader

# Setup logging for better visibility into the script's execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CLEANED_GNPS_LIBRARY_URL = "https://zenodo.org/records/11566051/files/cleaned_gnps_library.mgf?download=1"
LOTUS_METADATA_URL = "https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz"
DOWNLOAD_DIR = "monolith/downloads"

def download_files():
    """Downloads necessary files for processing."""
    downloader = BaseDownloader()
    
    try:
        logging.info("Downloading cleaned GNPS library...")
        downloader.download(CLEANED_GNPS_LIBRARY_URL, os.path.join(DOWNLOAD_DIR, "cleaned_gnps_library.mgf"))
        logging.info("Downloading LOTUS metadata...")
        downloader.download(LOTUS_METADATA_URL, os.path.join(DOWNLOAD_DIR, "taxo_db_metadata.csv.gz"))
        logging.info("Files downloaded successfully.")
    except Exception as e:
        logging.error(f"Error downloading files: {e}")
        raise

def load_spectrums(file_path: str) -> list:
    """Loads and returns spectrums from an MGF file."""
    try:
        logging.info(f"Loading spectrums from {file_path}...")
        spectrums = list(load_from_mgf(file_path))
        logging.info(f"{len(spectrums)} spectrums found and imported.")
        return spectrums
    except Exception as e:
        logging.error(f"Error loading spectrums from {file_path}: {e}")
        raise

def plot_instrument_counts(spectrums: list):
    """Plots a bar chart of instrument_type occurrences."""
    logging.info("Extracting and plotting instrument types...")
    instrument_types = [spectrum.metadata.get('instrument_type') for spectrum in spectrums]
    instrument_counts = Counter(instrument_types)

    # Plot instrument occurrences
    plt.bar(instrument_counts.keys(), instrument_counts.values())
    plt.xlabel('Instrument Type')
    plt.ylabel('Count')
    plt.title('Instrument Type Occurrences')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    logging.info("Instrument type plot completed.")
    return instrument_counts

def filter_spectrums_by_inchikey(spectrums: list, valid_inchikeys: Set[str]) -> list:
    """Filters spectrums that have matching InChIKeys in the metadata."""
    logging.info("Filtering spectrums by InChIKey...")
    filtered_spectrums = [spectrum for spectrum in tqdm(spectrums, desc="Filtering spectrums") 
                          if spectrum.metadata.get('inchikey') in valid_inchikeys]
    logging.info(f"{len(filtered_spectrums)} spectrums found with matching InChIKey.")
    return filtered_spectrums

def get_instrument_rank(spectrum, instrument_rank: Dict[str, int], instrument_priority: list[str]):
    """Returns the rank of the instrument type based on priority."""
    instrument_type = spectrum.metadata.get('instrument_type')
    return instrument_rank.get(instrument_type, len(instrument_priority))

def filter_by_instrument_priority(spectrums: list, instrument_rank: Dict[str, int], instrument_priority: list[str]) -> list:
    """Filters to retain only one representative spectrum per InChIKey."""
    logging.info("Selecting highest-priority spectrum for each InChIKey...")
    spectra_by_inchikey = defaultdict(list)
    for spectrum in spectrums:
        inchikey = spectrum.metadata.get('inchikey')
        if inchikey:
            spectra_by_inchikey[inchikey].append(spectrum)
    
    final_spectrums = []
    for spectra in tqdm(spectra_by_inchikey.values(), desc="Selecting spectra by instrument priority"):
        best_spectrum = min(spectra, key=lambda s: get_instrument_rank(s, instrument_rank, instrument_priority))
        final_spectrums.append(best_spectrum)
    
    logging.info(f"{len(final_spectrums)} spectrums selected after filtering by instrument priority.")
    return final_spectrums

def count_unique_inchikeys(spectrums: list) -> int:
    """Counts the number of unique InChIKeys in a list of spectrums."""
    inchikeys = [spectrum.metadata.get('inchikey') for spectrum in spectrums]
    return len(set(inchikeys))

def main():
    # Download necessary files
    download_files()
    
    # Load spectrums from file
    mgf_path = os.path.join(DOWNLOAD_DIR, "cleaned_gnps_library.mgf")
    spectrums = load_spectrums(mgf_path)

    # Extract and plot instrument counts
    instrument_counts = plot_instrument_counts(spectrums)
    instrument_priority = [instrument for instrument, _ in instrument_counts.most_common()]
    instrument_rank = {instrument: rank for rank, instrument in enumerate(instrument_priority)}
    
    # Load LOTUS metadata
    logging.info("Loading LOTUS metadata...")
    lotus_metadata = pd.read_csv(os.path.join(DOWNLOAD_DIR, "taxo_db_metadata.csv.gz"), low_memory=False)
    valid_inchikeys = set(lotus_metadata['structure_inchikey'].dropna().unique())
    logging.info(f"{len(valid_inchikeys)} unique InChIKeys found in LOTUS metadata.")
    
    # Filter spectrums by InChIKey
    filtered_spectrums = filter_spectrums_by_inchikey(spectrums, valid_inchikeys)
    
    # Retain only the highest-priority spectrum per InChIKey
    final_filtered_spectrums = filter_by_instrument_priority(filtered_spectrums, instrument_rank, instrument_priority)

    # Save the final filtered spectrums
    logging.info(f"Saving final filtered spectrums to {os.path.join(DOWNLOAD_DIR, 'final_filtered_spectrums.mgf')}...")
    save_as_mgf(final_filtered_spectrums, os.path.join(DOWNLOAD_DIR, "final_filtered_spectrums.mgf"))
    
    logging.info(f"Processing complete: {len(final_filtered_spectrums)} unique spectrums returned after filtering.")
    
    # Check for duplicates
    assert count_unique_inchikeys(final_filtered_spectrums) == len(final_filtered_spectrums), \
        "Duplicate InChIKeys found in the final_filtered_spectrums."
    
    logging.info("Final check: No duplicate InChIKeys detected.")

if __name__ == "__main__":
    main()
