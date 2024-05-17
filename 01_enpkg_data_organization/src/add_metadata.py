"""Argument parser """
import os
import yaml
import pandas as pd
from pathlib import Path
from lxml import etree


os.chdir(os.getcwd())

p = Path(__file__).parents[1]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)


sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])

path = os.path.normpath(sample_dir_path)
print(path)
samples_dir = [directory for directory in os.listdir(path)]
print(samples_dir)

for sample_directory in samples_dir:
    metadata_file_path = os.path.join(
        path, sample_directory, sample_directory + "_metadata.tsv"
    )
    print(metadata_file_path)
    metadata = pd.read_csv(metadata_file_path, sep="\t")
    print(metadata)





    metadata.to_csv(metadata_file_path, sep="\t", index=False)