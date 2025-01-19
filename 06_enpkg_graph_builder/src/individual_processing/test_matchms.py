
import os
import pandas as pd
import numpy as np
from matchms.importing import load_from_mgf

#load spectra 
path_data  = r"C:\Users\quirosgu\Desktop\ttl_collections"
file_mgf = os.path.join(path_data, "LQ-01-61-78_features_ms2_pos.mgf")
spectrums = list(load_from_mgf(file_mgf))

print(f"{len(spectrums)} spectrums found and imported")

#inspect spectra

numbers_of_peaks = [len(s.peaks.mz) for s in spectrums]


#preprocess spectra
from matchms.filtering import default_filters
from matchms.filtering import add_losses
from matchms.filtering import add_precursor_mz
from matchms.filtering import add_parent_mass


def spectrum_processing(spectrum):
    spectrum = default_filters(spectrum)
    spectrum = add_losses(spectrum)
    spectrum = add_precursor_mz(spectrum)
    spectrum = add_parent_mass(spectrum)
    return spectrum

spectrum_processing(spectrums[0])