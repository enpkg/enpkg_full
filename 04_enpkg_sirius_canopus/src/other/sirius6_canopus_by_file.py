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

sirius_command_base = f'"{path_to_sirius}" --input {{file}} --output {{output_name}} --cores=10 --maxmz=800 --recompute config --IsotopeSettings.filter=true --FormulaSearchDB=BIO --Timeout.secondsPerTree=0 --FormulaSettings.enforced=HCNOP --AdductSettings.detectable=[[M+Na]+,[M+H3N+H]+,[M-H4O2+H]+,[M+K]+,[M+H]+,[M-H2O+H]+] --UseHeuristic.mzToUseHeuristicOnly=650 --AlgorithmProfile=qtof --IsotopeMs2Settings=IGNORE --MS2MassDeviation.allowedMassDeviation=10.0ppm --NumberOfCandidatesPerIon=1 --UseHeuristic.mzToUseHeuristic=300 --FormulaSettings.detectable=B,Cl,Br,Se,S --NumberOfCandidates=10 --ZodiacNumberOfConsideredCandidatesAt300Mz=10 --ZodiacRunInTwoSteps=true --ZodiacEdgeFilterThresholds.minLocalConnections=10 --ZodiacEdgeFilterThresholds.thresholdFilter=0.95 --ZodiacEpochs.burnInPeriod=2000 --ZodiacEpochs.numberOfMarkovChains=10 --ZodiacNumberOfConsideredCandidatesAt800Mz=50 --ZodiacEpochs.iterations=20000 --AdductSettings.enforced=, --AdductSettings.fallback=[[M+Na]+,[M-H+K+K]+,[M+K]+,[M+H]+,[M-H2O+H]+] --FormulaResultThreshold=true --InjectElGordoCompounds=true --StructureSearchDB=BIO'

# Login to Sirius using environment variables for username and password
sirius_login_command = f'"{path_to_sirius}" login --user-env={sirius_user_env} --password-env={sirius_password_env}'

os.environ['SIRIUS_USERNAME'] = 'luis.guerrero@unige.ch'
os.environ['SIRIUS_PASSWORD'] = 'Suisse271289'

# Run the login command
subprocess.run(sirius_login_command, shell=True, env=my_env)

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

# Function to launch SIRIUS job (including Canopus) on a file
def compute_sirius(file, output_name):
    sirius_command = f'{sirius_command_base} -i "{file}" -o "{output_name}"'
    print(f"Running command: {sirius_command}")
    result = subprocess.run(sirius_command, shell=True, env=my_env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error in SIRIUS command: {result.stderr}")
        raise Exception(f"SIRIUS command failed with return code {result.returncode}")
    else:
        print(f"Command succeeded: {result.stdout}")

# Process each sample directory
for directory in tqdm(samples_dir):
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except (FileNotFoundError, NotADirectoryError):
        continue
    
    # Check if the sample type is "sample" and not QC or Blank
    if metadata['sample_type'][0] == 'sample':   
        if ionization == 'pos': 
            sirius_mgf_path = os.path.join(path, directory, ionization, directory + '_sirius_pos.mgf')
        elif ionization == 'neg':    
            sirius_mgf_path = os.path.join(path, directory, ionization, directory + '_sirius_neg.mgf')
        else:
            raise ValueError("ionization parameter must be pos or neg")   
        
        output_folder = os.path.join(path, directory, ionization, directory + '_' + output_suffix)        
        
        # Check if recompute is needed
        if (recompute is False) and os.path.isdir(output_folder):
            print(f"Skipped already computed sample: {directory}")          
            continue
        else:
            if os.path.isdir(output_folder):
                shutil.rmtree(output_folder)
            
            # Compute SIRIUS
            print(f"Computing Sirius on sample: {directory}")
            compute_sirius(sirius_mgf_path, output_folder)
            
            # Zip the outputs if requested
            if zip_output:
                if os.path.exists(output_folder):
                    for dir in os.listdir(output_folder):
                        if os.path.isdir(os.path.join(output_folder, dir)):
                            shutil.make_archive(os.path.join(output_folder, dir), 'zip', os.path.join(output_folder, dir))
                            shutil.rmtree(os.path.join(output_folder, dir))
                else:
                    print(f"Error: Output folder not found for {directory}: {output_folder}")
                          
            # Save parameters to a YAML file
            with open(os.path.join(output_folder, 'params.yml'), 'w') as file:
                yaml.dump(params_list, file)

            print(f"Sample: {directory} done")
