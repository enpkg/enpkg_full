from pathlib import Path
import os
import shutil
from tqdm import tqdm
import yaml
from rdflib import Graph, Namespace
import pandas as pd
import sys
from concurrent.futures import ProcessPoolExecutor
import git
import traceback

# Import custom functions
sys.path.append(os.path.join(Path(__file__).parents[1], "functions"))
from hash_functions import get_hash

# Set working directory to the repository root
repo_root = Path(__file__).parents[2]
os.chdir(repo_root)

# Function to substitute variables in YAML
def substitute_variables(config):
    """Recursively substitute placeholders in the YAML configuration."""
    def substitute(value, context):
        if isinstance(value, str):
            while any(f"${{{key}}}" in value for key in context):
                for key, replacement in context.items():
                    value = value.replace(f"${{{key}}}", str(replacement))
        return value

    def recurse_dict(d, context):
        for key, value in d.items():
            if isinstance(value, dict):
                recurse_dict(value, context)
            else:
                d[key] = substitute(value, context)

    # Context for substitution
    context = {
        "general.root_data_path": config.get("general", {}).get("root_data_path", ""),
        "general.treated_data_path": config.get("general", {}).get("treated_data_path", ""),
        "general.polarity": config.get("general", {}).get("polarity", ""),
    }
    recurse_dict(config, context)
    return config

# Load parameters
user_yaml_path = "../params/user.yml"
if not os.path.exists(user_yaml_path):
    raise FileNotFoundError(f"No {user_yaml_path}: copy from ../params/template.yml and modify according to your needs")

with open(user_yaml_path) as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute placeholders in the YAML parameters
params_list_full = substitute_variables(params_list_full)

# Extract relevant paths and settings
sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
polarity = params_list_full["general"]["polarity"]
version = params_list_full["assay-batch"]["version"]
kg_uri = params_list_full["graph-builder"]["kg_uri"]
ns_kg = Namespace(kg_uri)
prefix = params_list_full["graph-builder"]["prefix"]
module_uri = params_list_full["graph-builder"]["module_uri"]
ns_module = Namespace(module_uri)
prefix_module = params_list_full["graph-builder"]["prefix_module"]
wd_namespace = params_list_full["graph-builder"]["wd_namespace"]
WD = Namespace(wd_namespace)

# Ensure the sample directory exists
if not os.path.exists(sample_dir_path):
    raise FileNotFoundError(f"Sample directory path not found: {sample_dir_path}")

# Define RDF files to merge for each polarity
polarity_files = {
    "pos": [
        f"rdf/metadata_enpkg_pos.{output_format}",
        f"rdf/metadata_module_enpkg_pos.{output_format}",
        f"rdf/assay_batch_pos.{output_format}",
    ],
    "neg": [
        f"rdf/metadata_enpkg_neg.{output_format}",
        f"rdf/metadata_module_enpkg_neg.{output_format}",
        f"rdf/assay_batch_neg.{output_format}",
    ],
}

files = polarity_files.get(polarity)
if not files:
    raise ValueError(f"Invalid polarity: {polarity}. Must be 'pos' or 'neg'.")

# Process individual directories
def process_directory(directory):
    """Process a single sample directory."""
    #rdf_dir = sample_dir_path / directory / "rdf"
    try:
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")
        if not os.path.isfile(metadata_path):
            print(f"Skipping {directory}: Missing metadata file.")
            return f"Skipped {directory} due to missing metadata file."

        metadata = pd.read_csv(metadata_path, sep="\t")
        massive_id = metadata["massive_id"].iloc[0]

        #identify existing files
        existing_files = [
            os.path.join(sample_dir_path, directory, file_path)
            for file_path in files if os.path.isfile(os.path.join(sample_dir_path, directory, file_path))
        ]

        if not existing_files:
            print(f"No RDF files to merge for {directory}.")
            return f"Skipped {directory}, no RDF files to merge."

        # Merge RDF files
        merged_graph = Graph()
        merged_graph.namespace_manager.bind(prefix, ns_kg)
        merged_graph.namespace_manager.bind(prefix_module, ns_module)
        merged_graph.namespace_manager.bind("wd", WD)

        for file_path in existing_files:
            with open(file_path, "r", encoding="utf8") as f:
                file_content = f.read()
                merged_graph.parse(data=file_content, format=output_format)
     
        # Remove old merged graphs matching massive_id and polarity
        rdf_dir = os.path.join(sample_dir_path, directory, 'rdf')
        for file in os.listdir(rdf_dir):
            # Check if the file starts with massive_id and includes the polarity
            if file.endswith(f"{directory}_metadata.{output_format}"):
                os.remove(os.path.join(rdf_dir, file))
                print(f"Deleted old RDF file: {file}")
                
        # Save merged graph
        pathout = os.path.join(sample_dir_path, directory, "rdf")
        merged_graph_path = os.path.join(
            pathout, f"{massive_id}_{polarity}_merged_graph_{directory}_metadata_{version}.{output_format}"
        )

        merged_graph.serialize(destination=merged_graph_path, format=output_format, encoding="utf-8")


        # Save graph parameters
        params_path = os.path.join(pathout, "graph_params.yaml")
        if os.path.isfile(params_path):
            with open(params_path, encoding='UTF-8') as file:
                params_list = yaml.load(file, Loader=yaml.FullLoader)
        else:
            params_list = {}
     
        params_list["graph-builder"] = params_list_full["graph-builder"]

        with open(params_path, "w", encoding="UTF-8") as file:
            yaml.dump(params_list, file)

        return f"Processed {directory}"
    
    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message

# Main function
def main():
    directories = [d for d in os.listdir(sample_dir_path) if not d.startswith('.') and os.path.isdir(os.path.join(sample_dir_path, d))]
    if not directories:
        print(f"No directories found in {sample_dir_path}. Ensure the path is correct and contains directories.")
        return

    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, directories)
        for result in results:
            if result:
                print(result)

if __name__ == "__main__":
    main()
