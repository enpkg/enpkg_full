import os
import yaml
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, XSD
from concurrent.futures import ProcessPoolExecutor
import traceback
import pandas as pd


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

    # Context for substitution
    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"]
    }
    recurse_dict(config, context)
    return config


# Load parameters from YAML
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    raise FileNotFoundError('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Apply substitution to resolve placeholders
params_list_full = substitute_variables(params_list_full)

# Extract relevant parameters
sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
ionization_mode = params_list_full["general"]["polarity"]
kg_uri = params_list_full["graph-builder"]["kg_uri"]
ns_kg = Namespace(kg_uri)
prefix = params_list_full["graph-builder"]["prefix"]

# Ensure the substituted `sample_dir_path` exists
if not os.path.exists(sample_dir_path):
    raise FileNotFoundError(f"Sample directory path not found: {sample_dir_path}")

def process_directory(directory):
    """Process a single directory."""
    try:
        sirius_param_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_WORKSPACE_SIRIUS", "params.yml")
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

        if not os.path.exists(sirius_param_path) or not os.path.exists(metadata_path):
            print(f"No params.yml or metadata.tsv for {directory}")
            return

        metadata = pd.read_csv(metadata_path, sep="\t")

        if metadata.sample_type[0] not in ['QC', 'Blank']:
            print(f"Processing sample: {directory}")
            # Add processing logic here
            # Save results

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)

def main():
    directories = [d for d in os.listdir(sample_dir_path) if os.path.isdir(os.path.join(sample_dir_path, d))]

    with ProcessPoolExecutor(max_workers=32) as executor:
        for _ in executor.map(process_directory, directories):
            pass

if __name__ == "__main__":
    main()
