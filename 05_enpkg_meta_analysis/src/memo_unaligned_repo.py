import memo_ms as memo
import os
import argparse
import datatable as dt
import pandas as pd
import numpy as np
import textwrap

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        Compute MEMO matrix for a set of unaligned mgf files.
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True, help='The path to the directory where samples folders to process are located')
parser.add_argument('--ionization', required=True, help="ionization mode to use to build the memo_matrix: pos, neg or both", type= str)
parser.add_argument('--min_relative_intensity', help="Minimal relative intensity to keep a peak max_relative_intensity, default 0.01", type= float, default= 0.01)
parser.add_argument('--max_relative_intensity', help="Maximal relative intensity to keep a peak max_relative_intensity, default 1", type= float, default= 1.0)
parser.add_argument('--min_peaks_required', help="Minimum number of peaks to keep a spectrum, default 10", type= int, default= 10)
parser.add_argument('--losses_from', help="Minimal m/z value for losses losses_to (int): maximal m/z value for losses, default 10", type= int, default= 10)
parser.add_argument('--losses_to', help="Maximal m/z value for losses losses_to (int): maximal m/z value for losses, default 200", type= int, default= 200)
parser.add_argument('--n_decimals', help="Number of decimal when translating peaks/losses into words, default 2", type= int, default= 2)
parser.add_argument('--filter_blanks', help="Remove blanks samples from the MEMO matrix", type= bool, default= False)
parser.add_argument('--word_max_occ_blanks', help="Set --filter_blanks to True to use. If word is present in more than n blanks, word is removed from MEMO matrix, default -1 (all words kept)", type= int, default= -1)
parser.add_argument('--output', required=True, help="Output name to use for the generated MEMO matrix", type= str)

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
ionization = args.ionization

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

if (args.filter_blanks is False) & (args.word_max_occ_blanks != -1):
    raise ValueError('Set --filter_blanks to True to use word_max_occ_blanks')
    
i = 0        
for (root, _, files) in os.walk(sample_dir_path, topdown=True):
    for file in files:                
        if file.endswith(pattern_to_match1):
            i += 1
print(f"Generating MEMO matrix from {i} input files.") 
            
memo_unaligned = memo.MemoMatrix()
memo_unaligned.memo_from_unaligned_samples(path_to_samples_dir=sample_dir_path, pattern_to_match=pattern_to_match1,
                                            min_relative_intensity=args.min_relative_intensity, max_relative_intensity=args.max_relative_intensity, min_peaks_required=args.min_peaks_required, 
                                            losses_from=args.losses_from, losses_to=args.losses_to, n_decimals=args.n_decimals)    
table = memo_unaligned.memo_matrix
if args.filter_blanks:
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
    
if args.word_max_occ_blanks != -1:
    excluded_features = count_null[count_null < (len(table_matched)-args.word_max_occ_blanks)].index
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
                                                min_relative_intensity=args.min_relative_intensity, max_relative_intensity=args.max_relative_intensity, min_peaks_required=args.min_peaks_required, 
                                                losses_from=args.losses_from, losses_to=args.losses_to, n_decimals=args.n_decimals)    
    table = memo_unaligned.memo_matrix
    if args.filter_blanks:
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
        
    if args.word_max_occ_blanks != -1:
        excluded_features = count_null[count_null < (len(table_matched)-args.word_max_occ_blanks)].index
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
datatable.to_csv(f"{PATH}/{args.output}.gz", compression="gzip")    
params = pd.DataFrame.from_dict(vars(args).items()).rename(columns={0:'parameter', 1:'value'})
included_samples_df = df = pd.DataFrame(index=[0], columns=['parameter', 'value'])
included_samples_df.loc[0, 'parameter'] = 'included_samples'
included_samples_df.loc[0, 'value'] = list(table1.filename)

params = pd.concat([params, included_samples_df], ignore_index=True)
params.to_csv(f"{PATH}/{args.output}_params.csv", index=False)

print(f'results are in {PATH}') 

    