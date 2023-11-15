from pathlib import Path
import os
import shutil
import argparse
import textwrap
from tqdm import tqdm
import gzip
import yaml

# These lines allows to make sure that we are placed at the repo directory level 
p = Path(__file__).parents[2]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['graph-builder']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

source_path = os.path.normpath(params_list_full['graph-builder']['sample_dir_path'])
target_path = os.path.normpath(params_list_full['graph-builder']['graph_output_dir_path'])
compress = params_list_full['graph-builder']['compress_outputs']

os.makedirs(target_path, exist_ok=True)

samples_dir = [directory for directory in os.listdir(source_path)]
df_list = []
for directory in tqdm(samples_dir):
    if os.path.isdir(os.path.join(source_path, directory, "rdf")):
        for file in [directory for directory in os.listdir(os.path.join(source_path, directory, "rdf"))]:
            if 'merged_graph' in file:
                file_name = file
                src = os.path.join(source_path, directory, "rdf", file_name)
    else:
        continue
    if os.path.isfile(src):
        dst = os.path.join(target_path, file_name)
        if compress:
            with open(src, 'rb') as f_in:
                file_out = os.path.join(dst) + '.gz'
                if not os.path.isfile(file_out):
                    with gzip.open(file_out, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copyfile(src, dst)
    else:
        continue
