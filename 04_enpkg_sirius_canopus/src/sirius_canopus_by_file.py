import os
import yaml
from pathlib import Path
import pandas as pd
import subprocess
import shutil
from tqdm import tqdm
import git


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


def compute_sirius(file, output_name, sirius_command_base, my_env):
    """Run SIRIUS computation for a given sample."""
    sirius_command = sirius_command_base.replace("{file}", file).replace("{output_name}", output_name)
    print(f"Running command: {sirius_command}")
    result = subprocess.run(sirius_command, shell=True, env=my_env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error in SIRIUS command: {result.stderr}")
        raise Exception(f"SIRIUS command failed with return code {result.returncode}")
    else:
        print(f"Command succeeded: {result.stdout}")


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

    # Login to SIRIUS
    sirius_login_command = [
        path_to_sirius, "login",
        "--user-env=SIRIUS_USERNAME", "--password-env=SIRIUS_PASSWORD"
    ]
    result = subprocess.run(sirius_login_command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Sirius login successful.")
    else:
        print(f"Error during Sirius login: {result.stderr}")

    # Capture SIRIUS version information
    sirius_version_str = subprocess.check_output([path_to_sirius, "--version"]).decode().split("\n")

    # Retrieve Git commit hash
    git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha

    # Update params_list with version information
    params_list_full["sirius"]["version_info"] = {
        "git_commit": git_commit_hash,
        "git_commit_link": f"https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}",
        "SIRIUS": sirius_version_str[0],
        "SIRIUS lib": sirius_version_str[1],
        "CSI:FingerID lib": sirius_version_str[2],
    }

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

            # Check if recompute is needed
            if not recompute and os.path.isdir(output_folder):
                print(f"Skipped already computed sample: {directory}")
                continue
            else:
                if os.path.isdir(output_folder):
                    shutil.rmtree(output_folder)

                # Compute SIRIUS
                print(f"Computing Sirius on sample: {directory}")
                compute_sirius(sirius_mgf_path, output_folder, sirius_command_base, os.environ)

                # Check if output folder was created
                if not os.path.exists(output_folder):
                    print(f"Error: Sirius did not create the output folder for {directory}.")
                    continue  # Skip this sample

                # Zip the outputs if requested
                if zip_output:
                    for dir in os.listdir(output_folder):
                        dir_path = os.path.join(output_folder, dir)
                        if os.path.isdir(dir_path):
                            shutil.make_archive(dir_path, "zip", dir_path)
                            shutil.rmtree(dir_path)

                # Save parameters to a YAML file
                with open(os.path.join(output_folder, "params.yml"), "w") as file:
                    yaml.dump(params_list_full, file)

                print(f"Sample: {directory} done.")
