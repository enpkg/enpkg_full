from pathlib import Path
import os
import shutil
from tqdm import tqdm
import gzip
import yaml

# Change to the appropriate working directory
p = Path(__file__).parents[2]
os.chdir(p)

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
if not os.path.exists("../params/user.yml"):
    raise FileNotFoundError("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")

with open("../params/user.yml") as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute placeholders
params_list_full = substitute_variables(params_list_full)

# Extract relevant paths and settings
sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
target_path = os.path.normpath(params_list_full["graph-builder"]["graph_output_dir_path"])
compress = params_list_full["graph-builder"]["compress_outputs"]
polarity = params_list_full["general"]["polarity"]

# Ensure output path substitution worked
if "${" in target_path:
    raise ValueError(f"Target path contains unresolved variables: {target_path}")

# Ensure target directory exists
os.makedirs(target_path, exist_ok=True)

# Process samples and copy files
samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]
for directory in tqdm(samples_dir, desc="Processing directories"):
    rdf_dir = os.path.join(sample_dir_path, directory, "rdf")
    if os.path.isdir(rdf_dir):
        for file in os.listdir(rdf_dir):
            if f'{polarity}_merged_graph' in file:
                file_name = file
                src = os.path.join(rdf_dir, file_name)
                if os.path.isfile(src):
                    dst = os.path.join(target_path, file_name)
                    if compress:
                        file_out = dst + ".gz"
                        if not os.path.isfile(file_out):
                            with open(src, 'rb') as f_in:
                                with gzip.open(file_out, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            print(f"Compressed and copied: {file_name} to {file_out}")
                        else:
                            print(f"Compressed file already exists: {file_out}")
                    else:
                        shutil.copyfile(src, dst)
                        print(f"Copied: {file_name} to {dst}")
