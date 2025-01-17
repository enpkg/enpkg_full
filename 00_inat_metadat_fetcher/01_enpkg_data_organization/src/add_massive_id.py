import os
import re
import yaml
import pandas as pd
from pathlib import Path


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
    }
    recurse_dict(config, context)
    return config


if __name__ == "__main__":
    os.chdir(os.getcwd())

    p = Path(__file__).parents[1]
    os.chdir(p)

    # Load YAML configuration
    if not os.path.exists("../params/user.yml"):
        print("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")
        exit()

    with open(r"../params/user.yml") as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Apply variable substitution
    params_list_full = substitute_variables(params_list_full)

    # Access parameters
    sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
    massive_id = params_list_full["massive-id-addition"]["massive_id"]

    # Debug: Print resolved parameters
    print(f"Resolved Sample Directory Path: {sample_dir_path}")
    print(f"Resolved MassIVE ID: {massive_id}")

    # Validate MassIVE ID format
    if not bool(re.match(r"MSV\d{9}$", massive_id)):
        raise ValueError("Invalid MassIVE ID, must be in format MSVXXXXXXXXX")

    # Process samples
    path = os.path.normpath(sample_dir_path)
    samples_dir = [directory for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]

    for sample_directory in samples_dir:
        metadata_file_path = os.path.join(
            path, sample_directory, f"{sample_directory}_metadata.tsv"
        )
        print(f"Processing metadata file: {metadata_file_path}")
        try:
            metadata = pd.read_csv(metadata_file_path, sep="\t")
            print(f"Before update, metadata:\n{metadata.head()}")
        except (FileNotFoundError, NotADirectoryError):
            print(f"Skipping {sample_directory}: Metadata file not found.")
            continue

        # Add MassIVE ID to metadata
        metadata["massive_id"] = massive_id
        metadata.to_csv(metadata_file_path, sep="\t", index=False)
        print(f"File saved for {sample_directory}: {metadata_file_path}")

        # Reload to verify changes
        reloaded_metadata = pd.read_csv(metadata_file_path, sep="\t")
        print(f"Reloaded metadata for {sample_directory}:\n{reloaded_metadata.head()}")
