
import pandas as pd
import glob
import os
import yaml
import git
from pathlib import Path

from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz
from matchms.filtering.require_minimum_number_of_peaks  import require_minimum_number_of_peaks 

# from spectral_db_loader import load_spectral_db
# from spectral_db_loader import load_clean_spectral_db
# from spectral_db_loader import save_spectral_db
# from spectral_lib_matcher import spectral_matching
# from molecular_networking import generate_mn
# from ms1_matcher import ms1_matcher
# from reweighting_functions import taxonomical_reponderator, chemical_reponderator
# from helpers import top_N_slicer, annotation_table_formatter_taxo, annotation_table_formatter_no_taxo
# from plotter import plotter_count, plotter_intensity
# from formatters import feature_intensity_table_formatter


import sys 
sys.path.append('../')

from src.molecular_networking.molecular_networking import generate_mn
from src.classes.abstract_msoutput import MgfOutput, MNOutput


spectra_file_path = '/home/allardpm/git_repos/ENPKG/enpkg_full/tests/data/output/dbgi_000065_01_01/pos/dbgi_000065_01_01_features_ms2_pos.mgf'

# Import query spectra
spectra_query = list(load_from_mgf(spectra_file_path))
spectra_query = [require_minimum_number_of_peaks(s, n_required=1) for s in spectra_query]
spectra_query = [add_precursor_mz(s) for s in spectra_query if s]


# Instantiate a MgfMSOutput object with the name of the MS output, the type of the MS output, the polarity of the MS output, the type of the MGF file and the list of spectra

mgf_ms_output = MgfOutput(ms_output_name="dbgi_000065_01_01", ms_output_polarity = "positive", ms_output_type="mgf", mgf_type="mzmine", spectrum_list=spectra_query)

# Return the spectrum list of the MgfMSOutput object

mgf_ms_output.get_spectrum_list()



# Generate a SimilarityNetwork object from the spectrum list of the MgfMSOutput object

ms_network = generate_mn(mgf_ms_output, 0.1, 0.7, 15, 10)


dir(ms_network)

ms_network.export_to_graphml("test.graphml")

    input_is = ms_network.get_input_file()