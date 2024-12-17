import os
import yaml
from pathlib import Path
import pandas as pd
import subprocess
import shutil
from tqdm import tqdm
import git

# Set up the environment
my_env = os.environ.copy()
my_env["GUROBI_HOME"] = "/prog/gurobi951/linux64/"

# Change to the parent directory
p = Path(__file__).parents[1]
os.chdir(p)

# Load the user parameters
with open(r'../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['sirius']

# Extract relevant paths and options
path_to_data = params_list_full['general']['treated_data_path']
path_to_sirius = params_list_full['sirius']['paths']['path_to_sirius']

sirius_version = params_list_full['sirius']['options']['sirius_version']
ionization = params_list_full['sirius']['options']['ionization']
sirius_command_arg = params_list_full['sirius']['options']['sirius_command_arg']
recompute = params_list_full['sirius']['options']['recompute']
zip_output = params_list_full['sirius']['options']['zip_output']
sirius_user_env = params_list_full['sirius']['options']['sirius_user_env']
sirius_password_env = params_list_full['sirius']['options']['sirius_password_env']

output_suffix = 'WORKSPACE_SIRIUS'

# Correctly quote the path to handle spaces
sirius_command_base = f'"{path_to_sirius}" {sirius_command_arg}'

# Set environment variables for SIRIUS login
os.environ['SIRIUS_USERNAME'] = 'luis.guerrero@unige.ch'
os.environ['SIRIUS_PASSWORD'] = 'Suisse271289'

# Run the login command
sirius_login_command = [
    path_to_sirius, "login",
    "--user-env=SIRIUS_USERNAME", "--password-env=SIRIUS_PASSWORD"
]

result = subprocess.run(sirius_login_command, capture_output=True, text=True)

if result.returncode == 0:
    print("Sirius login successful.")
else:
    print(f"Error during Sirius login: {result.stderr}")

# Capture the SIRIUS version information
sirius_version_str = subprocess.check_output([path_to_sirius, "--version"]).decode().split('\n')

# Retrieve the current Git commit hash
git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha

# Update params_list with version information in a dictionary format
params_list['version_info'] = {
    'git_commit': git_commit_hash,
    'git_commit_link': f'https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}',
    'SIRIUS': sirius_version_str[0],
    'SIRIUS lib': sirius_version_str[1],
    'CSI:FingerID lib': sirius_version_str[2]
}

# Function to launch SIRIUS + Canopus job on a file
def compute_sirius_canopus(file, output_name):
    # First step: Run the computational commands
    sirius_compute_command = sirius_command_base.replace("{file}", file).replace("{output_name}", output_name)
    print(f"Running computational command: {sirius_compute_command}")
    result = subprocess.run(sirius_compute_command, shell=True, env=my_env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error in SIRIUS computational command: {result.stderr}")
        raise Exception(f"SIRIUS computational command failed with return code {result.returncode}")
    else:
        print(f"Computational command succeeded: {result.stdout}")

        # Second step: Run 'write-summaries' command with specified format
        sirius_summaries_command = f'"{path_to_sirius}" write-summaries --output "{output_name}"'
        print(f"Running write-summaries command: {sirius_summaries_command}")
        result = subprocess.run(sirius_summaries_command, shell=True, env=my_env, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error in write-summaries command: {result.stderr}")
            raise Exception(f"write-summaries command failed with return code {result.returncode}")
        else:
            print(f"write-summaries command succeeded: {result.stdout}")

        # Check if summary files exist
        summary_files = [f for f in os.listdir(output_name) if f.endswith('.tsv') or f.endswith('.csv')]
        if not summary_files:
            print(f"Warning: No summary files found for {output_name}.")
        else:
            print(f"Summary files found for {output_name}: {summary_files}")

# List sample directories
path = os.path.normpath(path_to_data)
samples_dir = [directory for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]

# Process each sample directory
for directory in tqdm(samples_dir):
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except (FileNotFoundError, NotADirectoryError):
        print(f"Metadata not found for {directory}, skipping...")
        continue

    if metadata['sample_type'][0] == 'sample':
        if ionization == 'pos':
            sirius_mgf_path = os.path.join(path, directory, ionization, directory + '_sirius_pos.mgf')
        elif ionization == 'neg':
            sirius_mgf_path = os.path.join(path, directory, ionization, directory + '_sirius_neg.mgf')
        else:
            raise ValueError("Ionization parameter must be 'pos' or 'neg'")

        output_folder = os.path.join(path, directory, ionization, directory + '_' + output_suffix)

        # Check if recompute is needed
        if (recompute is False) and os.path.isdir(output_folder):
            print(f"Skipped already computed sample: {directory}")
            continue
        else:
            if os.path.isdir(output_folder):
                shutil.rmtree(output_folder)

            # Compute SIRIUS and Canopus
            print(f"Computing Sirius on sample: {directory}")
            compute_sirius_canopus(sirius_mgf_path, output_folder)

            # Check if output folder was created
            if not os.path.exists(output_folder):
                print(f"Error: Sirius did not create the output folder for {directory}.")
                continue  # Skip this sample

            # Zip the outputs if requested
            if zip_output:
                for dir in os.listdir(output_folder):
                    dir_path = os.path.join(output_folder, dir)
                    if os.path.isdir(dir_path):
                        shutil.make_archive(dir_path, 'zip', dir_path)
                        shutil.rmtree(dir_path)

            # Save parameters to a YAML file
            with open(os.path.join(output_folder, 'params.yml'), 'w') as file:
                yaml.dump(params_list, file)

            print(f"Sample: {directory} done")
