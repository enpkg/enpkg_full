import os
import sys
import yaml
import traceback
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, FOAF, XSD
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from tqdm import tqdm
import hashlib  # For get_hash
import git

# Hashing functions
def get_hash(file_path):
    """Generate a hash for a given file."""
    hash_obj = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):  # Read the file in chunks of 8KB
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_data(file_path):
    """Read the content of a file as a string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

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
ionization_mode = params_list_full['general']['polarity']
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

# Validate the sample directory path
print(f"Resolved sample_dir_path: {sample_dir_path}")
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    sys.exit(1)

samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]

# Process a single directory
def process_directory(directory):
    try:
        quant_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_features_quant_{ionization_mode}.csv")
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

        if not os.path.isfile(quant_path) or not os.path.isfile(metadata_path):
            print(f"The file: {quant_path} or {metadata_path} does not exist, skipping {directory}")
            return

        quant_table = pd.read_csv(quant_path, sep=',')
        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] == 'sample':
            g = Graph()
            g.namespace_manager.bind(prefix, ns_kg)

            # Processing LCMS and hash
            lcms_processing_params_path = None
            for file in os.listdir(os.path.join(sample_dir_path, directory, ionization_mode)):
                if file.startswith(f"{directory}_lcms_processing_params_{ionization_mode}"):
                    lcms_processing_params_path = os.path.join(sample_dir_path, directory, ionization_mode, file)

            if lcms_processing_params_path:
                hash_1 = get_hash(lcms_processing_params_path)
                data_1 = get_data(lcms_processing_params_path)
                # Add the hash and data to the graph as triples
                # Example: g.add(...)
                print(f"Processed LCMS parameters for {directory} with hash {hash_1}")

        # Additional processing...
        print(f"Processed directory: {directory}")

    except Exception as e:
        print(f"Error processing {directory}: {e}\n{traceback.format_exc()}")

# Main function for processing directories
def main():
    print(f"Processing directories in {sample_dir_path}")
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, samples_dir)
        for result in tqdm(results, desc="Processing directories"):
            pass

if __name__ == "__main__":
    main()
