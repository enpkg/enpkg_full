import pandas as pd
import glob
import os
import yaml
import git
from pathlib import Path

from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz
from matchms.filtering.require_minimum_number_of_peaks import require_minimum_number_of_peaks

from spectral_db_loader import load_clean_spectral_db
from spectral_lib_matcher import spectral_matching
from molecular_networking import generate_mn
from ms1_matcher import ms1_matcher
from reweighting_functions import taxonomical_reponderator, chemical_reponderator
from helpers import top_N_slicer, annotation_table_formatter_taxo, annotation_table_formatter_no_taxo
from plotter import plotter_count, plotter_intensity
from formatters import feature_intensity_table_formatter

pd.options.mode.chained_assignment = None


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
        "general.root_data_path": config['general']['root_data_path'],
        "general.polarity": config['general']['polarity'],
    }
    recurse_dict(config, context)
    return config


if __name__ == "__main__":
    os.chdir(os.getcwd())

    p = Path(__file__).parents[1]
    os.chdir(p)

    # Load parameters from YAML file
    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
        exit()

    with open(r'../params/user.yml') as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Perform variable substitution
    params_list_full = substitute_variables(params_list_full)

    # Extract parameters
    params_list = params_list_full['isdb']
    recompute = params_list['general_params']['recompute']
    ionization_mode = params_list_full['general']['polarity']
    repository_path = os.path.normpath(params_list_full['general']['treated_data_path'])
    taxo_db_metadata_path = params_list['paths']['taxo_db_metadata_path']
    spectral_db_pos_path = os.path.normpath(params_list['paths']['spectral_db_pos_path'])
    spectral_db_neg_path = os.path.normpath(params_list['paths']['spectral_db_neg_path'])
    adducts_pos_path = os.path.normpath(params_list['paths']['adducts_pos_path'])
    adducts_neg_path = os.path.normpath(params_list['paths']['adducts_neg_path'])
    parent_mz_tol = params_list['spectral_match_params']['parent_mz_tol']
    msms_mz_tol = params_list['spectral_match_params']['msms_mz_tol']
    min_score = params_list['spectral_match_params']['min_score']
    min_peaks = params_list['spectral_match_params']['min_peaks']
    mn_msms_mz_tol = params_list['networking_params']['mn_msms_mz_tol']
    mn_score_cutoff = params_list['networking_params']['mn_score_cutoff']
    mn_max_links = params_list['networking_params']['mn_max_links']
    mn_top_n = params_list['networking_params']['mn_top_n']
    top_to_output = params_list['reweighting_params']['top_to_output']
    ppm_tol_ms1 = params_list['reweighting_params']['ppm_tol_ms1']
    use_post_taxo = params_list['reweighting_params']['use_post_taxo']
    top_N_chemical_consistency = params_list['reweighting_params']['top_N_chemical_consistency']
    min_score_taxo_ms1 = params_list['reweighting_params']['min_score_taxo_ms1']
    min_score_chemo_ms1 = params_list['reweighting_params']['min_score_chemo_ms1']
    msms_weight = params_list['reweighting_params']['msms_weight']
    taxo_weight = params_list['reweighting_params']['taxo_weight']
    chemo_weight = params_list['reweighting_params']['chemo_weight']

    # Retrieve the current Git commit hash
    git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha
    params_list['version_info'] = {
        'git_commit': git_commit_hash,
        'git_commit_link': f'https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}'
    }

###### START #####

# Iteration over samples directory to count samples with required input files

samples_dir = [directory for directory in os.listdir(repository_path)]
print(f'{len(samples_dir)} directories were detected in the input directory. They will be checked for minimal requirements.')

for sample_dir in samples_dir[:]:
    # if sample_dir != ".DS_Store":
    try:
        metadata_file_path = os.path.join(repository_path, sample_dir, sample_dir + '_metadata.tsv')
        metadata = pd.read_csv(metadata_file_path, sep='\t')
    except FileNotFoundError:
        samples_dir.remove(sample_dir)
        continue
    except NotADirectoryError:
        samples_dir.remove(sample_dir)
        continue
    
    # Check if sample_type == sample
    if metadata['sample_type'][0] == 'sample':
        pass
    else:
        print(sample_dir + " is a QC or a blank sample, it is removed from the processing list.")
        samples_dir.remove(sample_dir)
        continue

    # Check if MS/MS spectra are present 
    if os.path.isfile(os.path.join(repository_path,sample_dir, ionization_mode, sample_dir + '_features_ms2_' + ionization_mode + '.mgf')):
        pass
    else:
        print(sample_dir + " has no MSMS data, it is removed from the processing list.")
        samples_dir.remove(sample_dir)
        continue

    # Check if features intensity table is present
    if os.path.isfile(os.path.join(repository_path,sample_dir, ionization_mode, sample_dir + '_features_quant_' + ionization_mode + '.csv')):
        pass
    else:
        print(sample_dir + " has no feature intensity table, it is removed from the processing list.")
        samples_dir.remove(sample_dir)
        continue
    if recompute == False :
        if os.path.isfile(os.path.join(repository_path, sample_dir, ionization_mode, 'isdb/config.yaml')):
            print(sample_dir + " has already been annotated through the ISDB, since the recompute option (user.yaml) is set to False it will be removed from the processing list.")
            samples_dir.remove(sample_dir)
    # else:
    #     continue

print(f'{len(samples_dir)} samples folder were found to be complete and will be processed.')

# if input("Do you wish to continue and process samples? (y/n)") != ("y"):
#     exit()
    
# Load spectral DB
if ionization_mode == 'pos':
    spectral_db = load_clean_spectral_db(spectral_db_pos_path)
elif ionization_mode == 'neg':
    spectral_db = load_clean_spectral_db(spectral_db_neg_path)

# Calculate min and max m/z value using user's tolerance for adducts search
if ionization_mode == 'pos':
    adducts_df = pd.read_csv(adducts_pos_path, compression='gzip', sep='\t')
elif ionization_mode == 'neg':
    adducts_df = pd.read_csv(adducts_neg_path, compression='gzip', sep='\t')
else:
    raise ValueError('ionization_mode parameter must be pos or neg')

adducts_df['min'] = adducts_df['adduct_mass'] - \
    int(ppm_tol_ms1) * (adducts_df['adduct_mass'] / 1000000)
adducts_df['max'] = adducts_df['adduct_mass'] + \
    int(ppm_tol_ms1) * (adducts_df['adduct_mass'] / 1000000)

# Load structures taxonomical data
if taxo_db_metadata_path.endswith('.csv.gz'):
    db_metadata = pd.read_csv(taxo_db_metadata_path, sep=',', compression='gzip', on_bad_lines='skip', low_memory=False)
elif taxo_db_metadata_path.endswith('.csv'):
    db_metadata = pd.read_csv(taxo_db_metadata_path, sep=',', on_bad_lines='skip', low_memory=False)
db_metadata['short_inchikey'] = db_metadata.structure_inchikey.str.split(
    "-", expand=True)[0]
db_metadata.reset_index(inplace=True)
    
# Processing
for sample_dir in samples_dir:
    
    metadata_file_path = os.path.join(repository_path, sample_dir, sample_dir + '_metadata.tsv')
    metadata = pd.read_csv(metadata_file_path, sep='\t')   
    spectra_file_path = os.path.join(repository_path,sample_dir, ionization_mode, sample_dir + '_features_ms2_' + ionization_mode + '.mgf')       
    feature_table_path = os.path.join(repository_path,sample_dir, ionization_mode, sample_dir + '_features_quant_' + ionization_mode + '.csv')
    feature_table = pd.read_csv(feature_table_path, sep=',')
        
    try:
        for file in os.listdir(os.path.join(repository_path, sample_dir, 'taxo_output')):
            if file.endswith("_taxo_metadata.tsv"):
                taxo_metadata_path = os.path.join(repository_path, sample_dir, 'taxo_output', file)
            else:
                pass
        taxo_metadata = pd.read_csv(taxo_metadata_path, sep='\t')       
    except FileNotFoundError:
        taxo_metadata = None
    except IndexError:
        taxo_metadata = None

    print('''
    Treating file: ''' + sample_dir
    )

    isdb_results_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/{sample_dir}_isdb_{ionization_mode}.tsv')
    mn_ci_ouput_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/molecular_network/{sample_dir}_mn_metadata_{ionization_mode}.tsv')
    repond_table_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/{sample_dir}_isdb_reweighted_{ionization_mode}.tsv')
    repond_table_flat_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/{sample_dir}_isdb_reweighted_flat_{ionization_mode}.tsv')
    mn_graphml_ouput_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/molecular_network/{sample_dir}_mn_{ionization_mode}.graphml')
    treemap_chemo_counted_results_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/{sample_dir}_treemap_chemo_counted_{ionization_mode}.html')
    treemap_chemo_intensity_results_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/{sample_dir}_treemap_chemo_intensity_{ionization_mode}.html')
    isdb_config_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/config.yaml')
    mn_config_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/molecular_network/config.yaml')
    isdb_folder_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/isdb/')
    mn_folder_path = os.path.normpath(f'{repository_path}/{sample_dir}/{ionization_mode}/molecular_network/')
    
    # Import query spectra
    spectra_query = list(load_from_mgf(spectra_file_path))
    spectra_query = [require_minimum_number_of_peaks(s, n_required=1) for s in spectra_query]
    spectra_query = [add_precursor_mz(s) for s in spectra_query if s]

    # Molecular networking
    print('''
    Molecular networking 
    ''')
    
    generate_mn(spectra_query, mn_graphml_ouput_path, mn_ci_ouput_path, mn_msms_mz_tol, mn_score_cutoff, mn_top_n, mn_max_links)
    with open(mn_config_path, "w") as f:
        yaml.dump(params_list, f)
    
    print('''
    Molecular Networking done
    ''')

    # ISDB
    #if ionization_mode == 'pos':
    # Spectral matching
    print('''
    Spectral matching
    ''')
    
    spectral_matching(spectra_query, spectral_db, parent_mz_tol,
        msms_mz_tol, min_score, min_peaks, isdb_results_path)
    
    print('''
    Spectral matching done
    ''')
    
    try:
        dt_isdb_results = pd.read_csv(isdb_results_path, sep='\t', \
            usecols=['msms_score', 'feature_id', 'reference_id', 'short_inchikey'], on_bad_lines='skip', low_memory=True)
    except ValueError:   
        with open(isdb_config_path, "w") as f:
            yaml.dump(params_list, f)
        continue
    # Add 'libname' column and rename msms_score column
    dt_isdb_results['libname'] = 'ISDB'

    # Load MN metadata
    clusterinfo_summary = pd.read_csv(mn_ci_ouput_path, sep='\t', usecols=['feature_id', 'precursor_mz', 'component_id'], \
        on_bad_lines='skip', low_memory=True)
    clusterinfo_summary.rename(columns={'precursor_mz': 'mz'}, inplace=True)

    dt_isdb_results = pd.merge(dt_isdb_results, clusterinfo_summary, on='feature_id')

    print('Number of features: ' + str(len(clusterinfo_summary)))
    print('Number of MS2 annotation: ' + str(len(dt_isdb_results)))
    print('Number of annotated features: ' + str(len(dt_isdb_results['feature_id'].unique())))
    
        # Save params 
        with open(isdb_config_path, "w") as f:
            yaml.dump(params_list, f)
        del(dt_isdb_results_chem_rew)
        del(dt_isdb_results, taxo_reweight)
        
    else: 
        print('''
        No annotation for file: ''' + sample_dir
        )
                
    print('''
    Finished file: ''' + sample_dir
    )