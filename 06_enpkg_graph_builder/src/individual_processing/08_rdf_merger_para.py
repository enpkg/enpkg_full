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
from concurrent.futures import ProcessPoolExecutor
import traceback


sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash

# These lines allows to make sure that we are placed at the repo directory level 
p = Path(__file__).parents[2]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['graph-builder']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']

# Create enpkg namespace
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

# Create enpkgmodule namespace
module_uri = params_list_full['graph-builder']['module_uri']
ns_module = rdflib.Namespace(module_uri)
prefix_module = params_list_full['graph-builder']['prefix_module']

WD = Namespace(params_list_full['graph-builder']['wd_namespace'])


path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]
df_list = []

files = [f"rdf/canopus_pos.{output_format}", f"rdf/canopus_neg.{output_format}", 
        f"rdf/features_pos.{output_format}", f"rdf/features_neg.{output_format}", 
        f"rdf/features_spec2vec_pos.{output_format}", f"rdf/features_spec2vec_neg.{output_format}",
        f"rdf/individual_mn_pos.{output_format}", f"rdf/individual_mn_neg.{output_format}",
        f"rdf/isdb_pos.{output_format}", f"rdf/isdb_neg.{output_format}",
        f"rdf/sirius_pos.{output_format}", f"rdf/sirius_neg.{output_format}",
        f"rdf/metadata_enpkg.{output_format}", f"rdf/metadata_module_enpkg.{output_format}",
        f"rdf/structures_metadata.{output_format}"]

def process_directory(directory):

    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    # try:
    #     metadata = pd.read_csv(metadata_path, sep='\t')
    # except FileNotFoundError:
    #     continue
    # except NotADirectoryError:
    #     continue
    # massive_id = metadata['massive_id'][0]

    try:
        if not os.path.isfile(metadata_path):
            print(f"Skipping {directory}, missing files.")
            return f"Skipped {directory} due to missing files."
            
        metadata = pd.read_csv(metadata_path, sep='\t')
        massive_id = metadata['massive_id'][0]
        # Iterate over the files and add their contents to the merged graph
        exist_files = []
        for file_path in files:
            if os.path.isfile(os.path.join(sample_dir_path, directory, file_path)):
                exist_files.append(os.path.join(sample_dir_path, directory, file_path))
        if len(exist_files) > 0:
            merged_graph = Graph()
            nm = merged_graph.namespace_manager
            nm.bind(prefix, ns_kg)
            nm.bind(prefix_module, ns_module)
            nm.bind("wd", WD)

            for file_path in exist_files:
                with open(file_path, "r", encoding="utf8") as f:
                    file_content = f.read()
                    merged_graph.parse(data=file_content, format=output_format)

            for file in os.listdir(os.path.join(os.path.join(sample_dir_path, directory, 'rdf'))):
                if file.startswith(massive_id):
                    os.remove(os.path.join(sample_dir_path, directory, 'rdf', file))
                    
            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            # Save the merged graph using the format specified by the user
            pathout_graph = os.path.normpath(os.path.join(pathout, f'{massive_id}_{directory}_merged_graph.{output_format}'))
            merged_graph.serialize(destination=pathout_graph, format=output_format, encoding="utf-8")

            hash_merged = get_hash(pathout_graph)
            # Save the merged graph using the format specified by the user
            
            pathout_graph_hash = os.path.normpath(os.path.join(pathout, f'{massive_id}_{directory}_merged_graph_{hash_merged}.{output_format}'))

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
                                {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})

            with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
                yaml.dump(params_list, file)
            
            print(f'Results are in : {pathout_graph_hash}')
    
    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message

# The main portion of your script would then use a ProcessPoolExecutor
# to process multiple directories in parallel.

# Assuming 'path' is the directory where all your sample directories are located

path = os.path.normpath(sample_dir_path)

samples_dir = [directory for directory in os.listdir(path) if not directory.startswith('.')]

def main():

    # Number of max workers (processes) can be adjusted to your machine's capability
    with ProcessPoolExecutor(max_workers=32) as executor:
        # The map method can help maintain the order of results
        results = executor.map(process_directory, samples_dir)

    # Output or further process your results
    for result in results:
        print(result)

# Ensure running main function when the script is executed
if __name__ == "__main__":
    main()
