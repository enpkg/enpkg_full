"""Submodule aiming to build the benchmarking datasets."""

from typing import Any, Dict, List, Optional
from downloaders import BaseDownloader
from matchms.importing import load_from_mgf
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import pandas as pd

cleaned_gnps_library_url = "https://zenodo.org/records/11566051/files/cleaned_gnps_library.mgf?download=1"
lotus_metadata_url = "https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz"

downloader = BaseDownloader()

downloader.download(
    cleaned_gnps_library_url,
    "downloads/cleaned_gnps_library.mgf",
)

downloader.download(
    lotus_metadata_url,
    "downloads/taxo_db_metadata.csv.gz",
)



path_data = os.path.join(os.path.dirname(os.getcwd()), "enpkg_full/monolith/downloads")
file_mgf = os.path.join(path_data, "cleaned_gnps_library.mgf")
spectrums = list(load_from_mgf(file_mgf))

print(f"{len(spectrums)} spectrums found and imported")


spectrums[0].metadata
spectrums[0].spectrum_hash()
spectrums[0].get("inchikey")

print(spectrums[0])


# Extract instrument_type from each spectrum's metadata
instrument_types = [spectrum.metadata.get('instrument_type') for spectrum in spectrums]

# Count occurrences of each instrument_type
instrument_counts = Counter(instrument_types)

# Print the count of each instrument_type
for instrument, count in instrument_counts.items():
    print(f"{instrument}: {count}")

# Print the count of each instrument_type by decreasing count
for instrument, count in instrument_counts.most_common():
    print(f"{instrument}: {count}")

# Plot a bar chart of instrument_type occurrences
plt.bar(instrument_counts.keys(), instrument_counts.values())
plt.xlabel('Instrument Type')
plt.ylabel('Count')
plt.title('Instrument Type Occurrences')
plt.xticks(rotation=45, ha='right')  # Rotate x labels for better readability
plt.tight_layout()
plt.show()


lotus_metadata: pd.DataFrame = pd.read_csv(
    "downloads/taxo_db_metadata.csv", low_memory=False
)


# Extract the unique structure_inchikey values from the lotus_metadata DataFrame
valid_inchikeys = set(lotus_metadata['structure_inchikey'].dropna().unique())

# Filter the spectrums list based on the inchikey in the metadata
filtered_spectrums = [spectrum for spectrum in spectrums 
                      if spectrum.metadata.get('inchikey') in valid_inchikeys]

print(f"{len(filtered_spectrums)} spectrums were found to have a matching InChIKey in the LOTUS metadata")

# Define the instrument priority based on your ordered list (most common first)

instrument_priority = [instrument for instrument, _ in instrument_counts.most_common()]


# Create a dictionary with instrument types and their priority rank
instrument_rank = {instrument: rank for rank, instrument in enumerate(instrument_priority)}

# Group spectra by inchikey
spectra_by_inchikey = defaultdict(list)
for spectrum in filtered_spectrums:
    inchikey = spectrum.metadata.get('inchikey')
    if inchikey:
        spectra_by_inchikey[inchikey].append(spectrum)

# Function to get the instrument rank for a given spectrum
def get_instrument_rank(spectrum):
    instrument_type = spectrum.metadata.get('instrument_type')
    return instrument_rank.get(instrument_type, len(instrument_priority))  # Use len() as fallback for low priority

# Filter to retain only one representative per inchikey
final_filtered_spectrums = []
for inchikey, spectra in spectra_by_inchikey.items():
    # Sort spectra by instrument rank and select the first one (highest-priority instrument)
    best_spectrum = min(spectra, key=get_instrument_rank)
    final_filtered_spectrums.append(best_spectrum)

# Now `final_filtered_spectrums` contains one representative spectrum per inchikey

print(f"{len(final_filtered_spectrums)} spectrums were returned after filtering for the highest-priority instrument type")

# We confirm that no duplicated InChIKeys are present in the final_filtered_spectrums

inchikeys = [spectrum.metadata.get('inchikey') for spectrum in final_filtered_spectrums]
assert len(inchikeys) == len(set(inchikeys)), "Duplicate InChIKeys found in the final_filtered_spectrums"

# In fact we create a function to count the number of unique InChIKeys in a list of spectrums

def count_unique_inchikeys(spectrums):
    inchikeys = [spectrum.metadata.get('inchikey') for spectrum in spectrums]
    return len(set(inchikeys))

# We test the function with the final_filtered_spectrums

assert count_unique_inchikeys(final_filtered_spectrums) == len(final_filtered_spectrums), "Duplicate InChIKeys found in the final_filtered_spectrums"


count_unique_inchikeys(final_filtered_spectrums)

count_unique_inchikeys(filtered_spectrums)

count_unique_inchikeys(spectrums)


