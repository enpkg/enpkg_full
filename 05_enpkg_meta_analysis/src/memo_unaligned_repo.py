import memo_ms as memo
import os
import argparse
import datatable as dt
import pandas as pd
import numpy as np
import textwrap
from pathlib import Path
import yaml


p = Path(__file__).parents[1]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['memo']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

sample_dir_path = os.path.normpath(params_list['sample_dir_path'])
ionization = params_list['ionization']
min_relative_intensity = params_list['min_relative_intensity']
max_relative_intensity = params_list['max_relative_intensity']
min_peaks_required = params_list['min_peaks_required']
losses_from = params_list['losses_from']
losses_to = params_list['losses_to']
n_decimals = params_list['n_decimals']
filter_blanks = params_list['filter_blanks']
word_max_occ_blanks = params_list['word_max_occ_blanks']
output = os.path.normpath(params_list['output'])

pattern_to_match2 = None
if ionization == 'pos':
    pattern_to_match1 = '_features_ms2_pos.mgf'
elif ionization == 'neg':
    pattern_to_match1 = '_features_ms2_neg.mgf'
elif ionization == 'both':
    pattern_to_match1 = '_features_ms2_pos.mgf'
    pattern_to_match2 = '_features_ms2_neg.mgf'
else:
    raise ValueError('ionization must be pos, neg or both')

if (filter_blanks is False) & (word_max_occ_blanks != -1):
    raise ValueError('Set --filter_blanks to True to use word_max_occ_blanks')
    
i = 0        
for (root, _, files) in os.walk(sample_dir_path, topdown=True):
    for file in files:
        print(file)                
        if file.endswith(pattern_to_match1):
            i += 1
print(f"Generating MEMO matrix from {i} input files.") 
            
memo_unaligned = memo.MemoMatrix()
memo_unaligned.memo_from_unaligned_samples(path_to_samples_dir=sample_dir_path, pattern_to_match=pattern_to_match1,
                                            min_relative_intensity=min_relative_intensity, max_relative_intensity=max_relative_intensity, min_peaks_required=min_peaks_required, 
                                            losses_from=losses_from, losses_to=losses_to, n_decimals=n_decimals)    
table = memo_unaligned.memo_matrix
if filter_blanks:
    samples_dir = [directory for directory in os.listdir(sample_dir_path)]
    blanks = []
    for directory in samples_dir:
        metadata_path = os.path.join(sample_dir_path, directory, directory + '_metadata.tsv')
        try:
            metadata = pd.read_csv(metadata_path, sep='\t', usecols=['sample_id', 'sample_type'])
        except IOError:
            pass
        else:
            if (metadata['sample_type'] == "blank").bool():
                blanks.append(metadata['sample_id'].values[0])
                blanks = list(set(blanks) & set(table.index))
    table_matched = table.loc[blanks]
    table_matched = table_matched.loc[:, (table_matched != 0).any(axis=0)]
    count_null = table_matched.replace(0, np.nan).isnull().sum()
    
if word_max_occ_blanks != -1:
    excluded_features = count_null[count_null < (len(table_matched)-word_max_occ_blanks)].index
    table = table.drop(excluded_features, axis=1)

    table = table.drop(blanks, axis=0)
    table = table.astype(float)
    table = table.loc[:, (table != 0).any(axis=0)]
    
if (ionization == 'pos') | (ionization == 'both'):
    table = table.add_suffix('_pos')
elif ionization == 'neg':
    table = table.add_suffix('_neg')
table1 = table.reset_index().rename(columns={'index': 'filename'})
print(table1.shape)
    
if pattern_to_match2 is not None:
    i = 0        
    for (root, _, files) in os.walk(sample_dir_path, topdown=True):
        for file in files:                
            if file.endswith(pattern_to_match2):
                i += 1
    print(f"Generating MEMO matrix from {i} input files.")                 
    memo_unaligned = memo.MemoMatrix()
    memo_unaligned.memo_from_unaligned_samples(path_to_samples_dir=sample_dir_path, pattern_to_match=pattern_to_match2,
                                                min_relative_intensity=min_relative_intensity, max_relative_intensity=max_relative_intensity, min_peaks_required=min_peaks_required, 
                                                losses_from=losses_from, losses_to=losses_to, n_decimals=n_decimals)    
    table = memo_unaligned.memo_matrix
    if filter_blanks:
        samples_dir = [directory for directory in os.listdir(sample_dir_path)]
        blanks = []
        for directory in samples_dir:
            metadata_path = os.path.join(sample_dir_path, directory, directory + '_metadata.tsv')
            try:
                metadata = pd.read_csv(metadata_path, sep='\t', usecols=['sample_id', 'sample_type'])
            except IOError:
                pass
            else:
                if (metadata['sample_type'] == "blank").bool():
                    blanks.append(metadata['sample_id'].values[0])
                    blanks = list(set(blanks) & set(table.index))
        table_matched = table.loc[blanks]
        table_matched = table_matched.loc[:, (table_matched != 0).any(axis=0)]
        count_null = table_matched.replace(0, np.nan).isnull().sum()
        
    if word_max_occ_blanks != -1:
        excluded_features = count_null[count_null < (len(table_matched)-word_max_occ_blanks)].index
        table = table.drop(excluded_features, axis=1)

        table = table.drop(blanks, axis=0)
        table = table.astype(float)
        table = table.loc[:, (table != 0).any(axis=0)]
    table = table.add_suffix('_neg')
    table2 = table.reset_index().rename(columns={'index': 'filename'})
    table1 = table1.merge(table2, on = 'filename')
    
# export
PATH = os.path.normpath(sample_dir_path + '/003_memo_analysis/')
if not os.path.exists(PATH):
    os.makedirs(PATH)

datatable = dt.Frame(table1)
datatable.to_csv(f"{PATH}/{output}.gz", compression="gzip")    
params = pd.DataFrame.from_dict(vars(args).items()).rename(columns={0:'parameter', 1:'value'})
included_samples_df = df = pd.DataFrame(index=[0], columns=['parameter', 'value'])
included_samples_df.loc[0, 'parameter'] = 'included_samples'
included_samples_df.loc[0, 'value'] = list(table1.filename)

params = pd.concat([params, included_samples_df], ignore_index=True)
params.to_csv(f"{PATH}/{output}_params.csv", index=False)

print(f'results are in {PATH}') 

    