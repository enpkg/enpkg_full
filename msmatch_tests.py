import re

from matchms.importing import load_from_mzml
from pyteomics import mzml


def extract_injection_mode(mzml_file):
    injection_mode = None
    with mzml.read(mzml_file) as reader:
        for spectrum in reader:
            print(spectrum)
            # lowest_mz = spectrum["lowest observed m/z"]
            # highest_mz = spectrum["highest observed m/z"]
            # print(f"lowest m/z: {lowest_mz}")
            # print(f"highest m/z: {highest_mz}")
            # Check if injection mode is available in spectrum metadata
            if "positive scan" in spectrum:
                injection_mode = "pos"
                # break
            elif "negative scan" in spectrum:
                injection_mode = "neg"
                # break
    return injection_mode


def extract_last_spectrum(mzml_file):
    spectrums = list(load_from_mzml(mzml_file))
    last_entry = spectrums[-1].metadata
    input_string = last_entry["title"]

    # Regular expression to extract last scan
    last_spectrum_pattern = r"scan=(\d+)"

    # Find the scan number
    last_spectrum_match = re.search(last_spectrum_pattern, input_string)
    if last_spectrum_match:
        last_spectrum = last_spectrum_match.group(1)
    else:
        last_spectrum = None
    return last_spectrum


def extract_source_file(mzml_file):
    spectrums = list(load_from_mzml(mzml_file))
    last_entry = spectrums[-1].metadata
    input_string = last_entry["title"]

    # Regular expression to extract filename
    filename_pattern = r'File:"([^"]+)"'

    # Find the filename
    filename_match = re.search(filename_pattern, input_string)
    if filename_match:
        filename = filename_match.group(1)
    else:
        filename = None
    return filename


# Replace 'your_file.mzML' with the path to your .mzML file
mzml_file = "20240307_EB_dbgi_001195_01_01.mzML"
injection_mode = extract_injection_mode(mzml_file)
filename = extract_source_file(mzml_file)
last_spectrum = extract_last_spectrum(mzml_file)
print("Injection mode:", injection_mode)
print(f"Filename: {filename}")
print(f"Last spectrum: {last_spectrum}")
