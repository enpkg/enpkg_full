
import pandas as pd
import glob
import os
import yaml
import git
from pathlib import Path

from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz
from matchms.filtering.require_minimum_number_of_peaks  import require_minimum_number_of_peaks 


import sys 
sys.path.append('../')

from src.spectrum_enrichers.molecular_networking.molecular_networking import generate_mn, sorted_connected_component_subgraphs
from src.classes.abstract_msoutput import MgfOutput, MNOutput


spectra_file_path = '/home/allardpm/git_repos/ENPKG/enpkg_full/tests/data/output/dbgi_000065_01_01/pos/dbgi_000065_01_01_features_ms2_pos.mgf'

# Import query spectra
spectra_query = list(load_from_mgf(spectra_file_path))
spectra_query = [require_minimum_number_of_peaks(s, n_required=1) for s in spectra_query]
spectra_query = [add_precursor_mz(s) for s in spectra_query if s]

# spectra_query = [1,2,3,4,5,6,7,8,9,10]

# Instantiate a MgfMSOutput object with the name of the MS output, the type of the MS output, the polarity of the MS output, the type of the MGF file and the list of spectra

mgf_ms_output = MgfOutput(ms_output_name="dbgi_000065_01_01", ms_output_polarity = "positive", ms_output_type="mgf", mgf_type="mzmine", spectrum_list=spectra_query)

# Return the spectrum list of the MgfMSOutput object

mgf_ms_output.get_spectrum_list()


# Generate a SimilarityNetwork object from the spectrum list of the MgfMSOutput object

ms_network = generate_mn(mgf_ms_output, 0.1, 0.7, 15, 10)


dir(ms_network)

mn = ms_network.get_ms_network()

mn.export_to_graphml("test.graphml")

# Get the input file
input_is = ms_network.get_input_file()

# Fetch spectrum list from the input file of the SimilarityNetwork object
ms_network.get_input_file().get_spectrum_list()








# os.makedirs(os.path.dirname(mn_ci_ouput_path), exist_ok=True)
# comp.to_csv(mn_ci_ouput_path, sep = '\t', index = False)


mn = ms_network.get_ms_network()

components = sorted_connected_component_subgraphs(mn.graph)

# # We also increment the key by one to start the numbering at one.
comp_dict = {idx + 1 : comp.nodes() for idx, comp in enumerate(components)}
attr = {n: {'component_id' : comp_id} for comp_id, nodes in comp_dict.items() for n in nodes}

comp = pd.DataFrame.from_dict(attr, orient = 'index')
comp.reset_index(inplace = True)
comp.rename(columns={'index': 'feature_id'}, inplace=True)
count = comp.groupby('component_id').count()
count['new_ci'] = np.where(count['feature_id'] > 1, count.index, -1)
new_ci = pd.Series(count.new_ci.values,index=count.index).to_dict()
comp['component_id'] = comp['component_id'].map(new_ci)
spectra_query_metadata_df = pd.DataFrame(s.metadata for s in spectra_query)
comp = comp.merge(spectra_query_metadata_df[['feature_id', 'precursor_mz']], how='left')

