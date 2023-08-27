import pandas as pd
import argparse
import textwrap
from pathlib import Path
import os
from pathlib import PurePath

p = Path(__file__).parents[1]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
         This script creates a <sample>_taxo_metadata.tsv file with the WD ID of the samples species and its OTT taxonomy
         --------------------------------
            You should just enter the path to the directory where samples folders are located
        '''))
parser.add_argument('-p', '--db_metadata_path', required=True,
                    help='The path to the database metadata')

args = parser.parse_args()
db_metadata_path = os.path.normpath(args.db_metadata_path)

if db_metadata_path.endswith('.csv.gz'):
    db_metadata = pd.read_csv(db_metadata_path, sep=',', compression='gzip', on_bad_lines='skip', low_memory=False)
elif db_metadata_path.endswith('.csv'):
    db_metadata = pd.read_csv(db_metadata_path, sep=',', on_bad_lines='skip', low_memory=False)

exact_masses = list(db_metadata[['structure_exact_mass']].drop_duplicates()['structure_exact_mass'])

adducts_masses_dic = pd.read_csv('data_loc/adducts.tsv', sep='\t',  index_col=0).squeeze("columns").to_dict()

results = []
for exact_mass in exact_masses:
    adducts_pos = {
        'pos_3_3proton' : (exact_mass + 3 * adducts_masses_dic['proton']) / 3,
        'pos_3_2proton1sodium' : (exact_mass + 2 * adducts_masses_dic['proton'] + adducts_masses_dic['sodium']) / 3,
        'pos_3_1proton2sodium' : (exact_mass + adducts_masses_dic['proton'] + 2 * adducts_masses_dic['sodium']) / 3,
        'pos_3_3sodium' : (exact_mass + 3 * adducts_masses_dic['sodium']) / 3,
        'pos_2_2proton' : (exact_mass + 2 * adducts_masses_dic['proton']) / 2,
        'pos_2_2proton1ammonium' : (exact_mass + 2 * adducts_masses_dic['proton'] + adducts_masses_dic['ammonium']) / 2,
        'pos_2_1proton1sodium' : (exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['sodium']) / 2,
        'pos_2_1magnesium' : (exact_mass + adducts_masses_dic['magnesium']) / 2,
        'pos_2_1proton1potassium' : (exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['potassium']) / 2,
        'pos_2_1calcium' : (exact_mass + adducts_masses_dic['calcium']) / 2,
        'pos_2_2proton1acetonitrile' : (exact_mass + 2 * adducts_masses_dic['proton'] + adducts_masses_dic['acetonitrile']) / 2,
        'pos_2_2sodium' : (exact_mass + 2 * adducts_masses_dic['sodium']) / 2,
        'pos_2_1iron' : (exact_mass + adducts_masses_dic['iron']) / 2,
        'pos_2_2proton2acetonitrile' : (exact_mass + 2 * adducts_masses_dic['proton'] + 2 * adducts_masses_dic['acetonitrile']) / 2,
        'pos_2_2proton3acetonitrile' : (exact_mass + 2 * adducts_masses_dic['proton'] + 3 * adducts_masses_dic['acetonitrile']) / 2,
        'pos_1_1proton' : exact_mass + adducts_masses_dic['proton'],
        'pos_1_1proton1ammonium' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['ammonium'],
        'pos_1_1sodium' : exact_mass + adducts_masses_dic['sodium'],
        'pos_1_minus1proton1magnesium' : exact_mass - adducts_masses_dic['proton'] + adducts_masses_dic['magnesium'],
        'pos_1_1proton1methanol' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['methanol'],
        'pos_1_1potassium' : exact_mass + adducts_masses_dic['potassium'],
        'pos_1_minus1proton1calcium' : exact_mass - adducts_masses_dic['proton'] + adducts_masses_dic['calcium'],
        'pos_1_1proton1acetonitrile' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['acetonitrile'],
        'pos_1_minus1proton2sodium' : exact_mass - adducts_masses_dic['proton'] + 2 * adducts_masses_dic['sodium'],
        'pos_1_1proton1ethylamine' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['ethylamine'],
        'pos_1_minus1proton1iron' : exact_mass - adducts_masses_dic['proton'] + adducts_masses_dic['iron'],
        'pos_1_1proton1isopropanol' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['isopropanol'],
        'pos_1_1sodium1acetonitrile' : exact_mass + adducts_masses_dic['sodium'] + adducts_masses_dic['acetonitrile'],
        'pos_1_minus1proton2potassium' : exact_mass - adducts_masses_dic['proton'] + 2 * adducts_masses_dic['potassium'],
        'pos_1_1proton1dmso' : exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['dmso'],
        'pos_1_1proton2acetonitrile' : exact_mass + adducts_masses_dic['proton'] + 2 * adducts_masses_dic['acetonitrile'],
        'pos_2MMg' : (2 * exact_mass + adducts_masses_dic['magnesium']) / 2,
        'pos_2MCa' : (2 * exact_mass + adducts_masses_dic['calcium']) / 2,
        'pos_2MFe' : (2 * exact_mass + adducts_masses_dic['iron']) / 2,
        'pos_2MH' : 2 * exact_mass + adducts_masses_dic['proton'],
        'pos_2MHNH3' : 2 * exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['ammonium'],
        'pos_2MNa' : 2 * exact_mass + adducts_masses_dic['sodium'],
        'pos_2MK' : 2 * exact_mass + adducts_masses_dic['potassium'],
        'pos_2MHCH3CN' : 2 * exact_mass + adducts_masses_dic['proton'] + adducts_masses_dic['acetonitrile'],
        'pos_2MCH3CNNa' : 2 * exact_mass + adducts_masses_dic['acetonitrile'] + adducts_masses_dic['sodium']
    }
    for key, value in adducts_pos.items():
        results.append((exact_mass, key, value))
        
results_pos = pd.DataFrame(results, columns=["exact_mass", "adduct", "adduct_mass"])  

results = []
for exact_mass in exact_masses:
    adducts_neg = {
        'neg_3_3proton' : (exact_mass - 3 * adducts_masses_dic['proton']) / 3,
        'neg_2_2proton' : ((exact_mass - 2 * adducts_masses_dic['proton']) / 2),
        'neg_1_minus1proton' : exact_mass - adducts_masses_dic['proton'],
        'neg_1_minus2proton1sodium' : exact_mass + adducts_masses_dic['sodium'] - 2 * adducts_masses_dic['proton'],
        'neg_1_1chlorine' : exact_mass + adducts_masses_dic['chlorine'],
        'neg_1_minus2proton1potassium' : exact_mass + adducts_masses_dic['potassium'] - 2 * adducts_masses_dic['proton'],
        'neg_1_minus1proton1formic' : exact_mass + adducts_masses_dic['formic'] - adducts_masses_dic['proton'],
        'neg_1_minus1proton1acetic' : exact_mass + adducts_masses_dic['acetic'] - adducts_masses_dic['proton'],
        'neg_1_minus2proton1sodium1formic' : exact_mass + adducts_masses_dic['formic'] + adducts_masses_dic['sodium'] - 2 * adducts_masses_dic['proton'],
        'neg_1_1bromine' : exact_mass + adducts_masses_dic['bromine'],
        'neg_1_minus1proton1tfa' : exact_mass + adducts_masses_dic['tfa'] - adducts_masses_dic['proton'],
        'neg_2MH' : 2 * exact_mass - adducts_masses_dic['proton'],
        'neg_2MFAH' : 2 * exact_mass + adducts_masses_dic['formic'] - adducts_masses_dic['proton'],
        'neg_2MACH' : 2 * exact_mass + adducts_masses_dic['acetic'] - adducts_masses_dic['proton'],
        'neg_3MH' : 3 * exact_mass - adducts_masses_dic['proton']
    }
    for key, value in adducts_neg.items():
        results.append((exact_mass, key, value))
        
results_neg = pd.DataFrame(results, columns=["exact_mass", "adduct", "adduct_mass"])  

adducts_pos = results_pos[['adduct']].drop_duplicates().rename(columns = {'adduct': 'adduct_pos'})
adducts_neg = results_neg[['adduct']].drop_duplicates().rename(columns = {'adduct': 'adduct_neg'})
params = pd.concat([adducts_pos, adducts_neg], axis=1)

#filename = db_metadata_path.split('\\')[-1].split('.')[0]

filename = PurePath(db_metadata_path).stem.split('.')[0]

path_pos = os.path.normpath(os.getcwd() + '/data_loc/' + filename + '/' + filename + '_adducts_pos.tsv.gz')
path_neg = os.path.normpath(os.getcwd() + '/data_loc/' + filename + '/' + filename + '_adducts_neg.tsv.gz')
path_params = os.path.normpath(os.getcwd() + '/data_loc/' + filename + '/' + filename + '_params.tsv')

os.makedirs(os.path.normpath(os.getcwd() +'/data_loc/' + filename), exist_ok=True)
#print("Filename is " + filename)
#print("Path is " + path_pos)
results_pos.to_csv(path_pos, sep = '\t', compression='gzip')
results_neg.to_csv(path_neg, sep = '\t', compression='gzip')
params.to_csv(path_params, sep = '\t')