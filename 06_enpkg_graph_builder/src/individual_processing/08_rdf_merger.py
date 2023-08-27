from rdflib import Graph, Namespace
import pandas as pd
from pathlib import Path
import os
from tqdm import tqdm
import rdflib
import argparse
import textwrap
import git
import yaml
import sys

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash

# These lines allows to make sure that we are placed at the repo directory level 
p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a unique RDF graph by sample (.ttl format) from multiples sample specific .rdf files.
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)

# Create enpkg namespace
kg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(kg_uri)
prefix_kg = "enpkg"

# Create enpkgmodule namespace
module_uri = "https://enpkg.commons-lab.org/module/"
ns_module = rdflib.Namespace(module_uri)
prefix_module = "enpkgmodule"
WD = Namespace('http://www.wikidata.org/entity/')

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]
df_list = []

files = ["rdf/canopus_pos.ttl", "rdf/canopus_neg.ttl", 
        "rdf/features_pos.ttl", "rdf/features_neg.ttl", 
        "rdf/features_spec2vec_pos.ttl", "rdf/features_spec2vec_neg.ttl",
        "rdf/individual_mn_pos.ttl", "rdf/individual_mn_neg.ttl",
        "rdf/isdb_pos.ttl", "rdf/isdb_neg.ttl",
        "rdf/sirius_pos.ttl", "rdf/sirius_neg.ttl",
        "rdf/metadata_enpkg.ttl", "rdf/metadata_module_enpkg.ttl",
        "rdf/structures_metadata.ttl"]

for directory in tqdm(samples_dir):
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    massive_id = metadata['massive_id'][0]
    
    # Iterate over the files and add their contents to the merged graph
    exist_files = []
    for file_path in files:
        if os.path.isfile(os.path.join(sample_dir_path, directory, file_path)):
            exist_files.append(os.path.join(sample_dir_path, directory, file_path))
    if len(exist_files) > 0:
        merged_graph = Graph()
        nm = merged_graph.namespace_manager
        nm.bind(prefix_kg, ns_kg)
        nm.bind(prefix_module, ns_module)
        nm.bind("wd", WD)

        for file_path in exist_files:
            with open(file_path, "r", encoding="utf8") as f:
                file_content = f.read()
                merged_graph.parse(data=file_content, format="ttl")

        for file in os.listdir(os.path.join(os.path.join(sample_dir_path, directory, 'rdf'))):
            if file.startswith(massive_id):
                os.remove(os.path.join(sample_dir_path, directory, 'rdf', file))
                
        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout_graph = os.path.normpath(os.path.join(pathout, f'{massive_id}_{directory}_merged_graph.ttl'))
        merged_graph.serialize(destination=pathout_graph, format="ttl", encoding="utf-8")

        hash_merged = get_hash(pathout_graph)
        pathout_graph_hash = os.path.normpath(os.path.join(pathout, f'{massive_id}_{directory}_merged_graph_{hash_merged}.ttl'))
        if os.path.isfile(pathout_graph_hash):
            os.remove(pathout_graph_hash)
        os.rename(pathout_graph, pathout_graph_hash)
        
        # Save parameters:
        params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
        if os.path.isfile(params_path):
            with open(params_path, encoding='UTF-8') as file:    
                params_list = yaml.load(file, Loader=yaml.FullLoader) 
        else:
            params_list = {}  
                
        params_list.update({f'{directory}_merged_graph':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                            {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})

        with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
            yaml.dump(params_list, file)
        
        print(f'Results are in : {pathout_graph_hash}')
    
    else:
        continue
