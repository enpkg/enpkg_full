"""Argument parser """
import argparse
import os
import re
import textwrap
import yaml
import pandas as pd
from pathlib import Path


os.chdir(os.getcwd())

p = Path(__file__).parents[1]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['massive-id-addition']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']


sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
massive_id = params_list_full['massive-id-addition']['massive_id']


# Check if format of MassIVE ID is correct:
if not bool(re.match("MSV\d\d\d\d\d\d\d\d\d$", massive_id)):
    raise ValueError("Invalid MassIVE ID, must be in format MSVXXXXXXXXX")

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]

for sample_directory in samples_dir:
    metadata_file_path = os.path.join(
        path, sample_directory, sample_directory + "_metadata.tsv"
    )
    try:
        metadata = pd.read_csv(metadata_file_path, sep="\t")
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    metadata["massive_id"] = massive_id
    metadata.to_csv(metadata_file_path, sep="\t", index=False)
