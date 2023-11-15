import os
import yaml
from pathlib import Path
import pandas as pd
import subprocess
import shutil
from tqdm import tqdm
import git

my_env = os.environ.copy()
my_env["GUROBI_HOME"] = "/prog/gurobi951/linux64/"

p = Path(__file__).parents[1]
os.chdir(p)
#from canopus import Canopus

with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['sirius']


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

sirius_command = path_to_sirius + ' ' + sirius_command_arg
sirius_login_command = path_to_sirius + ' ' + 'login' + ' ' + '--user-env=' + sirius_user_env + ' ' + '--password-env=' + sirius_password_env

""" Parameters used """
sirius_version_str = subprocess.check_output([path_to_sirius, "--version"]).decode().split('\n')
params_list.update({'version_info':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                                    {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'},
                                    {'SIRIUS':sirius_version_str[0]},
                                    {'SIRIUS lib':sirius_version_str[1]},
                                    {'CSI:FingerID lib':sirius_version_str[2]}]})

if sirius_version == 4:
    from canopus import Canopus
    
# Lauch sirius+ canopus job on a file
def compute_sirius_canopus(file, output_name):
    subprocess.run(sirius_command.format(file=file, output_name=output_name), shell = True, env=my_env)
                      
path = os.path.normpath(path_to_data)
samples_dir = [directory for directory in os.listdir(path)]

# In both case we need to login using the credentials

subprocess.run(sirius_login_command, shell = True, env=my_env)


for directory in tqdm(samples_dir):
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue 
    
    # Check if the sample type is sample and not QC or Blank
    if metadata['sample_type'][0] == 'sample':   
        if ionization == 'pos': 
            sirius_mgf_path = os.path.join(path, directory,ionization, directory + '_sirius_pos.mgf')
        elif ionization == 'neg':    
            sirius_mgf_path = os.path.join(path, directory,ionization, directory + '_sirius_neg.mgf')
        else:
            raise ValueError("ionization parameter must be pos or neg")   
        
        output_folder = os.path.join(path, directory, ionization, directory + '_' + output_suffix)        
        if (recompute is False) & (os.path.isdir(output_folder)):
            print(f"Skipped already computed sample: {directory}")          
            continue
        else:
            if os.path.isdir(output_folder):
                shutil.rmtree(output_folder)
            
            if sirius_version == 4:
                print(f"Computing Sirius on sample: {directory}")
                compute_sirius_canopus(sirius_mgf_path, output_folder)
                print(f"Computing NPC Canopus on sample: {directory}")            
                C = Canopus(sirius=output_folder)
                C.npcSummary().to_csv(os.path.join(output_folder, "npc_summary.csv"))            
                print(f"Zipping outputs on sample: {directory}")
                
            elif sirius_version == 5:
                print(f"Computing Sirius on sample: {directory}")
                compute_sirius_canopus(sirius_mgf_path, output_folder)
            else:
                raise ValueError("sirius_version parameter must be 4 or 5")
            
            if zip_output:
                for dir in [directory for directory in os.listdir(output_folder)]:
                    if os.path.isdir(os.path.join(output_folder, dir)):
                        shutil.make_archive(os.path.join(output_folder, dir), 'zip', os.path.join(output_folder, dir))
                        shutil.rmtree(os.path.join(output_folder, dir))
                          
            with open(os.path.join(path, directory, ionization, directory + '_' + output_suffix, 'params.yml'), 'w') as file:
                yaml.dump(params_list, file)

            print(f"Sample: {directory} done")
                
