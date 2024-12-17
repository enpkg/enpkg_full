from rdflib import Graph, Namespace
import pandas as pd
from pathlib import Path
import os
from concurrent.futures import ProcessPoolExecutor
import yaml
import git
import sys
import traceback

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash

# Change to the appropriate working directory
p = Path(__file__).parents[2]
os.chdir(p)

# Function to substitute variables in YAML
def substitute_variables(config):
    """Recursively substitute placeholders in the YAML configuration."""
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

    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
    }
    recurse_dict(config, context)
    return config

# Load parameters
if not os.path.exists("../params/user.yml"):
    raise FileNotFoundError("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")

with open("../params/user.yml") as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute placeholders
params_list_full = substitute_variables(params_list_full)

# Extract relevant paths and settings
sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
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

# Define RDF files to merge
files = [
    f"rdf/canopus_pos.{output_format}", f"rdf/canopus_neg.{output_format}",
    f"rdf/features_pos.{output_format}", f"rdf/features_neg.{output_format}",
    f"rdf/features_spec2vec_pos.{output_format}", f"rdf/features_spec2vec_neg.{output_format}",
    f"rdf/individual_mn_pos.{output_format}", f"rdf/individual_mn_neg.{output_format}",
    f"rdf/isdb_pos.{output_format}", f"rdf/isdb_neg.{output_format}",
    f"rdf/sirius_pos.{output_format}", f"rdf/sirius_neg.{output_format}",
    f"rdf/metadata_enpkg.{output_format}", f"rdf/metadata_module_enpkg.{output_format}",
    f"rdf/structures_metadata.{output_format}"
]

# Process a single directory
def process_directory(directory):
    try:
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")
        if not os.path.isfile(metadata_path):
            print(f"Skipping {directory}, missing metadata file.")
            return f"Skipped {directory} due to missing metadata file."

        metadata = pd.read_csv(metadata_path, sep='\t')
        massive_id = metadata['massive_id'][0]

        # Identify existing RDF files
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

        # Remove old merged graphs
        rdf_dir = os.path.join(sample_dir_path, directory, 'rdf')
        for file in os.listdir(rdf_dir):
            if file.startswith(massive_id):
                os.remove(os.path.join(rdf_dir, file))

        # Save the merged graph
        pathout = os.path.join(sample_dir_path, directory, "rdf")
        os.makedirs(pathout, exist_ok=True)
        merged_graph_path = os.path.join(pathout, f"{massive_id}_{directory}_merged_graph.{output_format}")
        merged_graph.serialize(destination=merged_graph_path, format=output_format, encoding="utf-8")

        # Add hash to the filename
        hash_merged = get_hash(merged_graph_path)
        hashed_graph_path = os.path.join(pathout, f"{massive_id}_{directory}_merged_graph_{hash_merged}.{output_format}")
        os.rename(merged_graph_path, hashed_graph_path)

        # Save graph parameters
        params_path = os.path.join(pathout, "graph_params.yaml")
        if os.path.isfile(params_path):
            with open(params_path, encoding='UTF-8') as file:
                params_list = yaml.load(file, Loader=yaml.FullLoader)
        else:
            params_list = {}

        git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha
        params_list[f"{directory}_merged_graph"] = {
            "git_commit": git_commit_hash,
            "git_commit_link": f"https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}"
        }
        params_list["graph-builder"] = params_list_full["graph-builder"]

        with open(params_path, "w", encoding="UTF-8") as file:
            yaml.dump(params_list, file)

        print(f"Merged graph saved at: {hashed_graph_path}")
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
