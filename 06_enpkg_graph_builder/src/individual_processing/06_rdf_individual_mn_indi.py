import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, XSD, RDFS
import networkx as nx
import argparse
import textwrap
from pathlib import Path
from tqdm import tqdm
import sys
import git
import yaml

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from samples' individual MNs 
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
            - Ionization mode to process
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')
parser.add_argument('-ion', '--ionization_mode', required=True,
                    help='The ionization mode to process')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
ionization_mode = args.ionization_mode

path = os.path.normpath(sample_dir_path)

samples_dir = [directory for directory in os.listdir(path)]
df_list = []
for directory in tqdm(samples_dir):
    
    g = Graph()
    nm = g.namespace_manager
    kg_uri = "https://enpkg.commons-lab.org/kg/"
    ns_kg = rdflib.Namespace(kg_uri)
    prefix = "enpkg"
    nm.bind(prefix, ns_kg)

    graph_path = os.path.join(path, directory, ionization_mode, 'molecular_network', directory + '_mn_' + ionization_mode + '.graphml')
    graph_metadata_path = os.path.join(path, directory, ionization_mode, 'molecular_network', directory + '_mn_metadata_' + ionization_mode + '.tsv')
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        graph = nx.read_graphml(graph_path)
        metadata = pd.read_csv(metadata_path, sep='\t')
        graph_metadata = pd.read_csv(graph_metadata_path, sep='\t')
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    for node in graph.edges(data=True):
        s = node[0]
        t = node[1]
        cosine = node[2]['weight']
        
        mass_diff = abs(float(graph_metadata[graph_metadata.feature_id == int(s)]['precursor_mz'].values[0] - graph_metadata[graph_metadata.feature_id == int(t)]['precursor_mz'].values[0]))
        component_index = graph_metadata[graph_metadata.feature_id == int(s)]['component_id'].values[0]

        usi_s = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode + '.mgf:scan:' + str(s) 
        s_feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi_s)
        usi_t = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode + '.mgf:scan:' + str(t) 
        t_feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi_t)
        
        ci_node = rdflib.term.URIRef(kg_uri + metadata.sample_id[0]+ '_fbmn_' + ionization_mode + '_componentindex_' + str(component_index))
        g.add((s_feature_id, ns_kg.has_fbmn_ci, ci_node))
        g.add((t_feature_id, ns_kg.has_fbmn_ci, ci_node))
        
        link_node = rdflib.term.URIRef(kg_uri + 'lcms_feature_pair_' + usi_s + '_' + usi_t)
        g.add((link_node, RDF.type, ns_kg.LFpair))
        g.add((link_node, ns_kg.has_cosine, rdflib.term.Literal(cosine, datatype=XSD.float)))
        g.add((link_node, ns_kg.has_mass_difference, rdflib.term.Literal(mass_diff, datatype=XSD.float)))

        mn_params_path = os.path.join(path, directory, ionization_mode, 'molecular_network', 'config.yaml')
        hash_1 = get_hash(mn_params_path)
        data_1 = get_data(mn_params_path)
        mn_params_hash = rdflib.term.URIRef(kg_uri + "mn_params_" + hash_1)
        g.add((link_node, ns_kg.has_mn_params, mn_params_hash))
        g.add((mn_params_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
        del(hash_1, data_1)
        
        if graph_metadata[graph_metadata.feature_id == int(s)]['precursor_mz'].values[0] > graph_metadata[graph_metadata.feature_id == int(t)]['precursor_mz'].values[0]:
            g.add((link_node, ns_kg.has_member_1, s_feature_id))
            g.add((link_node, ns_kg.has_member_2, t_feature_id))
        else:
            g.add((link_node, ns_kg.has_member_1, t_feature_id))
            g.add((link_node, ns_kg.has_member_2, s_feature_id))

    pathout = os.path.join(sample_dir_path, directory, "rdf/")
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.normpath(os.path.join(pathout, f'individual_mn_{ionization_mode}.ttl'))
    g.serialize(destination=pathout, format="ttl", encoding="utf-8")
    
    # Save parameters:
    params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
    
    if os.path.isfile(params_path):
        with open(params_path, encoding='UTF-8') as file:    
            params_list = yaml.load(file, Loader=yaml.FullLoader) 
    else:
        params_list = {}  
            
    params_list.update({f'individual_mn_{ionization_mode}':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                        {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})
    
    with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
        yaml.dump(params_list, file)
        
    print(f'Results are in : {pathout}')  
    