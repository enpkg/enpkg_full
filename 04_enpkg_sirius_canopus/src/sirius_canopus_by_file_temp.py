import os
import yaml
from pathlib import Path
import pandas as pd
import subprocess
import shutil
from tqdm import tqdm


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


def compute_sirius(file, local_output_name, sirius_command_base, my_env):
    """Run SIRIUS computation for a given sample."""
    sirius_command = sirius_command_base.replace("{file}", file).replace("{output_name}", local_output_name)
    print(f"Running SIRIUS command:\n{sirius_command}\n")
    
    result = subprocess.run(sirius_command, shell=True, env=my_env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error in SIRIUS command: {result.stderr}")
        print(f"Command output: {result.stdout}")
        raise Exception(f"SIRIUS command failed with return code {result.returncode}")
    else:
        print(f"SIRIUS command succeeded:\n{result.stdout}")


def export_summaries(local_output_folder, sirius_executable, my_env):
    """Export summaries forcibly if they are missing."""
    summaries_path = os.path.join(local_output_folder, "summaries")
    if not os.path.exists(summaries_path):
        print(f"Summaries missing in {local_output_folder}. Attempting forced export...")
        try:
            export_command = f'"{sirius_executable}" export-summaries --input {local_output_folder} --output {summaries_path}'
            result = subprocess.run(export_command, shell=True, env=my_env, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error in forced summary export: {result.stderr}")
                raise Exception(f"Summary export failed with return code {result.returncode}")
            else:
                print(f"Summaries successfully exported to {summaries_path}.")
        except Exception as e:
            print(f"Error exporting summaries: {e}")
            return
    else:
        print(f"Summaries already exist in {summaries_path}.")

    # Ensure summaries_path exists before listing contents
    if os.path.isdir(summaries_path):
        exported_files = [f for f in os.listdir(summaries_path) if os.path.isfile(os.path.join(summaries_path, f))]
        if exported_files:
            print(f"Exported summaries for {local_output_folder}: {exported_files}")
        else:
            print(f"No summary files found in {summaries_path}.")
    else:
        print(f"Summary directory {summaries_path} does not exist.")


if __name__ == "__main__":
    # Change to the parent directory
    p = Path(__file__).parents[1]
    os.chdir(p)

    # Load user parameters
    if not os.path.exists("../params/user.yml"):
        print("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")
        exit()

    with open(r"../params/user.yml") as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Perform variable substitution
    params_list_full = substitute_variables(params_list_full)

    # Extract relevant parameters
    path_to_data = params_list_full["general"]["treated_data_path"]
    path_to_sirius = params_list_full["sirius"]["paths"]["path_to_sirius"]
    sirius_version = params_list_full["sirius"]["options"]["sirius_version"]
    ionization = params_list_full["general"]["polarity"]

    # Dynamically select the correct commands based on version and ionization
    if sirius_version == 6:
        sirius_command_args = params_list_full["sirius"]["options"]["sirius_6_command_args"]
    elif sirius_version == 5:
        sirius_command_args = params_list_full["sirius"]["options"]["sirius_5_command_args"]
    else:
        raise ValueError("Unsupported SIRIUS version. Please specify 5 or 6 in the configuration.")

    sirius_command_arg = sirius_command_args["pos"] if ionization == "pos" else sirius_command_args["neg"]
    sirius_command_base = f'"{path_to_sirius}" {sirius_command_arg}'

    # Other options
    recompute = params_list_full["sirius"]["options"]["recompute"]
    zip_output = params_list_full["sirius"]["options"]["zip_output"]

    # Set environment variables for SIRIUS login
    os.environ["SIRIUS_USERNAME"] = params_list_full["sirius"]["options"]["sirius_user_env"]
    os.environ["SIRIUS_PASSWORD"] = params_list_full["sirius"]["options"]["sirius_password_env"]

    # Temporary local output directory
    local_tmp_dir = "/tmp/sirius_outputs"
    os.makedirs(local_tmp_dir, exist_ok=True)
    print(f"Temporary local directory: {local_tmp_dir}")

    # List sample directories
    path = os.path.normpath(path_to_data)
    samples_dir = [directory for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]

    # Process each sample directory
    for directory in tqdm(samples_dir):
        metadata_path = os.path.join(path, directory, directory + "_metadata.tsv")
        try:
            metadata = pd.read_csv(metadata_path, sep="\t")
        except (FileNotFoundError, NotADirectoryError):
            print(f"Metadata not found for {directory}, skipping...")
            continue

        if metadata["sample_type"][0] == "sample":
            sirius_mgf_path = os.path.join(
                path, directory, ionization, f"{directory}_sirius_{ionization}.mgf"
            )
            output_folder = os.path.join(path, directory, ionization, f"{directory}_WORKSPACE_SIRIUS")
            local_output_folder = os.path.join(local_tmp_dir, f"{directory}_WORKSPACE_SIRIUS")

            # Debug information
            print(f"Processing sample: {directory}")
            print(f"Input file path: {sirius_mgf_path}")
            print(f"Local output folder: {local_output_folder}")
            print(f"Expected output folder: {output_folder}")

            # Check if the input file exists
            if not os.path.exists(sirius_mgf_path):
                print(f"Error: Input file {sirius_mgf_path} does not exist. Skipping sample {directory}.")
                continue

            # Check if recompute is needed
            if not recompute and os.path.isdir(output_folder):
                print(f"Skipped already computed sample: {directory}")
                continue
            else:
                if os.path.isdir(local_output_folder):
                    shutil.rmtree(local_output_folder)

                # Compute SIRIUS
                try:
                    compute_sirius(sirius_mgf_path, local_output_folder, sirius_command_base, os.environ)
                except Exception as e:
                    print(f"Error processing sample {directory}: {e}")
                    continue

                # Check if output folder was created locally
                if not os.path.exists(local_output_folder):
                    print(f"Error: Sirius did not create the local output folder for {directory}.")
                    continue  # Skip this sample

                # Check and export summaries if missing
                try:
                    export_summaries(local_output_folder, path_to_sirius, os.environ)
                except Exception as e:
                    print(f"Error exporting summaries for {directory}: {e}")
                    continue

                # Zip the outputs if requested
                if zip_output:
                    for dir in os.listdir(local_output_folder):
                        dir_path = os.path.join(local_output_folder, dir)
                        if os.path.isdir(dir_path):
                            shutil.make_archive(dir_path, "zip", dir_path)
                            shutil.rmtree(dir_path)

                # Transfer the results to the final output directory
                try:
                    os.makedirs(os.path.dirname(output_folder), exist_ok=True)
                    shutil.move(local_output_folder, output_folder)
                    print(f"Results for {directory} successfully moved to: {output_folder}")
                except Exception as e:
                    print(f"Error moving results for {directory}: {e}")
                    print(f"Results remain in local temporary directory: {local_output_folder}")

                print(f"Sample: {directory} done.")
