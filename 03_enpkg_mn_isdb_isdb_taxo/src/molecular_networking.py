import os
import numpy as np
import pandas as pd
from matchms import calculate_scores
from matchms.similarity import ModifiedCosine
from matchms.networking import SimilarityNetwork
import networkx as nx

def connected_component_subgraphs(G):
            for c in nx.connected_components(G):
                yield G.subgraph(c)
             
def sorted_connected_component_subgraphs(G):
            for c in sorted(nx.connected_components(G), key=len, reverse=True):
                yield G.subgraph(c)
                
def generate_mn(spectra_query, mn_graphml_ouput_path, mn_ci_ouput_path, mn_msms_mz_tol, mn_score_cutoff, mn_top_n, mn_max_links):
    """Generate a Molecular Network from MS/MS spectra using the modified cosine score

    Args:
        spectra_query (list): A list of matchms spectra objects
        mn_graphml_ouput_path (str): Path to export the .graphml MN file
        mn_ci_ouput_path (str): Path to export the .tsv MN metadata file
        mn_msms_mz_tol (float): Tolerance in Da for MS/MS fragments matching
        mn_score_cutoff (float): Minimal modified cosine score for edge creation
        mn_top_n (int): Consider edge between spectrumA and spectrumB if score falls into top_n for spectrumA or spectrumB \
            (link_method="single"), or into top_n for spectrumA and spectrumB (link_method="mutual"). From those potential links, \
            only max_links will be kept, so top_n must be >= max_links.
        mn_max_links (int): Maximum number of links to add per node.
    """    
    score = ModifiedCosine(tolerance=float(mn_msms_mz_tol))
    scores = calculate_scores(spectra_query, spectra_query, score, is_symmetric=True)
    ms_network = SimilarityNetwork(identifier_key="scans", score_cutoff = mn_score_cutoff, top_n = mn_top_n, max_links = mn_max_links, link_method = 'mutual')
    ms_network.create_network(scores, score_name="ModifiedCosine_score")
    os.makedirs(os.path.dirname(mn_graphml_ouput_path), exist_ok=True)
    ms_network.export_to_graphml(mn_graphml_ouput_path)
    # Here we use the sorted_connected_component_subgraphs in ordere to make sure that components are sequentially labelled from the largest to the smallest
    components = sorted_connected_component_subgraphs(ms_network.graph)
    # We also increment the key by one to start the numbering at one.
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
    os.makedirs(os.path.dirname(mn_ci_ouput_path), exist_ok=True)
    comp.to_csv(mn_ci_ouput_path, sep = '\t', index = False)