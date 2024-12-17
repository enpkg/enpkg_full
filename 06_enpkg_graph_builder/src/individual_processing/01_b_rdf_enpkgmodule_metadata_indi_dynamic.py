import os
import sys
import yaml
import traceback
from pathlib import Path
from rdflib import Graph, Namespace, RDF
from tqdm import tqdm
import pandas as pd

# Substitute variables function
def substitute_variables(config):
    """Recursively substitute variables in the YAML configuration."""
    def substitute(value, context):
        if isinstance(value, str):
            for key, replacement in context.items():
                value = value.replace(f"${{{key}}}", replacement)
        return value

    def recurse_dict(d, context):
        for key, value in d.items():
            if isinstance(value, dict):
                recurse_dict(value, context)
            else:
                d[key] = substitute(value, context)

    # Context for substitution
    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config


# Load parameters and substitute variables
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    sys.exit(1)

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Apply variable substitution
params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
WD = Namespace(params_list_full['graph-builder']['wd_namespace'])
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
module_uri = params_list_full['graph-builder']['module_uri']
ns_module = Namespace(module_uri)
prefix_module = params_list_full['graph-builder']['prefix_module']
target_chembl_url = params_list_full['graph-builder']['target_chembl_url']
source_taxon_header = params_list_full['graph-builder']['source_taxon_header']
source_id_header = params_list_full['graph-builder']['source_id_header']

# Validate the sample directory path
print(f"Resolved sample_dir_path: {sample_dir_path}")
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    sys.exit(1)

samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]

def process_directory(directory):
    print(f"Processing directory: {directory}")
    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix, ns_kg)
    nm.bind(prefix_module, ns_module)

    try:
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")
        print(f"Looking for metadata file: {metadata_path}")

        if not os.path.exists(metadata_path):
            print(f"Metadata file not found for {directory}")
            return  # Skip this directory if metadata file is not found

        metadata = pd.read_csv(metadata_path, sep='\t')
        print(f"Metadata loaded for {directory}, columns: {metadata.columns}")

        sample = Namespace(kg_uri)[metadata.sample_id[0]]

        if metadata.sample_type[0] == 'sample':
            print(f"Processing sample for directory: {directory}")
            material_id = Namespace(kg_uri)[metadata[source_id_header][0]]

            # Dynamically create triples for all columns, including any bioassay columns
            for column in metadata.columns:
                if column not in ['sample_id', 'sample_type']:
                    column_name = column.replace(' ', '_')
                    value = metadata[column][0]
                    if pd.notna(value):
                        value_clean = str(value).replace(' ', '_')
                        g.add((material_id, getattr(ns_module, f'has_{column_name}'), Namespace(module_uri)[value_clean]))
                        print(f"Added triple for {column_name} with value {value_clean}")

        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.join(pathout, f"metadata_module_enpkg.{output_format}")
        
        if len(g) > 0:
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            print(f"Results are in: {pathout}")
        else:
            print(f"No data to serialize for {directory}")
    
    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message


# Main function for processing directories
def main():
    print(f"Processing directories in {sample_dir_path}")
    for directory in tqdm(samples_dir, desc="Processing directories"):
        process_directory(directory)


if __name__ == "__main__":
    main()
