import pandas as pd
import numpy as np
import zipfile
import glob
import os
import sys
import time
import shlex
import subprocess
import contextlib
import io
from tqdm import tqdm
from tqdm import tqdm_notebook
from tqdm.contrib import tzip
from opentree import OT
import json
from pandas import json_normalize
import yaml
from pandas import json_normalize
import networkx as nx
import os.path
from os import path

from matchms.importing import load_from_mgf
from matchms.exporting import save_as_mgf
from matchms.filtering import default_filters
from matchms.filtering import normalize_intensities
from matchms.filtering import select_by_intensity
from matchms.filtering import select_by_mz
from matchms.similarity import PrecursorMzMatch
from matchms import calculate_scores
from matchms.similarity import CosineGreedy
from matchms.similarity import ModifiedCosine
from matchms.networking import SimilarityNetwork
# from ms2deepscore import MS2DeepScore
# from ms2deepscore.models import load_model


from plotter import *
from loaders import *
from formatters import *



pd.options.mode.chained_assignment = None

os.chdir(os.getcwd())

# for debug ony should be commented later
from pathlib import Path
p = Path(__file__).parents[1]
print(p)
os.chdir(p)

# you can copy the configs/default/default.yaml to configs/user/user.yaml

with open (r'configs/user/user.yaml') as file:    
    params_list = yaml.load(file, Loader=yaml.FullLoader)

repository_path = params_list['paths'][0]['repository_path']
spectra_suffix = params_list['paths'][1]['spectra_suffix']
metadata_sample_suffix = params_list['paths'][2]['metadata_sample_suffix']
feature_table_suffix = params_list['paths'][3]['feature_table_suffix']
metadata_path = params_list['paths'][4]['metadata_path']
db_file_path = params_list['paths'][5]['db_file_path']
adducts_pos_path = params_list['paths'][6]['adducts_pos_path']
adducts_neg_path = params_list['paths'][7]['adducts_neg_path']

parent_mz_tol = params_list['spectral_match_params'][0]['parent_mz_tol']
msms_mz_tol = params_list['spectral_match_params'][1]['msms_mz_tol']
min_score = params_list['spectral_match_params'][2]['min_score']
min_peaks = params_list['spectral_match_params'][3]['min_peaks']
match_score = params_list['spectral_match_params'][4]['match_score']
model_path = params_list['spectral_match_params'][5]['model_path']

mn_parent_mz_tol = params_list['networking_params'][0]['mn_parent_mz_tol']
mn_msms_mz_tol = params_list['networking_params'][1]['mn_msms_mz_tol']
mn_score_cutoff = params_list['networking_params'][2]['mn_score_cutoff']
mn_max_links = params_list['networking_params'][3]['mn_max_links']
mn_top_n = params_list['networking_params'][4]['mn_top_n']
mn_score = params_list['networking_params'][5]['mn_score']
mn_model_path = params_list['networking_params'][6]['mn_model_path']

top_to_output= params_list['repond_params'][0]['top_to_output']
ppm_tol = params_list['repond_params'][1]['ppm_tol']
polarity = params_list['repond_params'][2]['polarity']
organism_header = params_list['repond_params'][3]['organism_header']
sampletype_header = params_list['repond_params'][4]['sampletype_header']
use_post_taxo = params_list['repond_params'][5]['use_post_taxo']
top_N_chemical_consistency = params_list['repond_params'][6]['top_N_chemical_consistency']
min_score_taxo_ms1 = params_list['repond_params'][7]['min_score_taxo_ms1']
min_score_chemo_ms1 = params_list['repond_params'][8]['min_score_chemo_ms1']

isdb_output_suffix = params_list['output_params'][0]['isdb_output_suffix']
mn_output_suffix = params_list['output_params'][1]['mn_output_suffix']
repond_table_suffix = params_list['output_params'][2]['repond_table_suffix']



# Defining functions 

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.StringIO()
    yield
    sys.stdout = save_stdout

def metadata_processing(spectrum):
    spectrum = default_filters(spectrum)
    return spectrum


def peak_processing(spectrum):
    spectrum = default_filters(spectrum)
    spectrum = normalize_intensities(spectrum)
    spectrum = select_by_intensity(spectrum, intensity_from=0.01)
    spectrum = select_by_mz(spectrum, mz_from=10, mz_to=1000)
    return spectrum

def connected_component_subgraphs(G):
            for c in nx.connected_components(G):
                yield G.subgraph(c)

###### START #####

print('Cleaning the spectral database metadata fields ...')

spectrums_db = list(load_from_mgf(db_file_path))


spectrums_db_cleaned = [metadata_processing(s) for s in spectrums_db]

print('A total of %s clean spectra were found in the spectral library.' % len(spectrums_db_cleaned))


if polarity == 'pos':
    adducts_df = pd.read_csv(adducts_pos_path, compression='gzip', sep='\t')
else:
    adducts_df = pd.read_csv(adducts_neg_path, compression='gzip', sep='\t')

adducts_df['min'] = adducts_df['adduct_mass'] - \
    int(ppm_tol) * (adducts_df['adduct_mass'] / 1000000)
adducts_df['max'] = adducts_df['adduct_mass'] + \
    int(ppm_tol) * (adducts_df['adduct_mass'] / 1000000)


repository_path_list = [x[0] for x in os.walk(repository_path)]
repository_path_list.remove(repository_path)

start_time = time.time()

for sample_dir in repository_path_list:

    sample = sample_dir.split(repository_path,1)[1]
    #os.chdir(sample_dir)

    if len(glob.glob(sample_dir+'/*'+spectra_suffix)) != 0 :
        spectra_file_path = glob.glob(sample_dir+'/*'+ spectra_suffix)[0]

    if len(glob.glob(sample_dir+'/*'+metadata_sample_suffix)) != 0 :
        metadata_sample_path = glob.glob(sample_dir +'/*' + metadata_sample_suffix)[0]
        samples_metadata = pd.read_csv(metadata_sample_path, sep='\t')
        
    if len(glob.glob(sample_dir+'/*'+feature_table_suffix)) != 0 :
        feature_table_path = glob.glob(sample_dir +'/*' + feature_table_suffix)[0]
        feature_table = pd.read_csv(feature_table_path, sep=',')
    else:
        continue
    
    if samples_metadata[sampletype_header][0] == 'sample':
        print('''
        Treating file: ''' + sample
        )

        isdb_results_path = sample_dir + '/' + sample + isdb_output_suffix + '.tsv'
        mn_ci_ouput_path = sample_dir + '/' + sample + mn_output_suffix + '_ci.tsv'
        repond_table_path = sample_dir + '/' + sample  + repond_table_suffix + '.tsv'
        repond_table_flat_path = sample_dir + '/' + sample + repond_table_suffix + '_flat.tsv'
        mn_graphml_ouput_path = sample_dir + '/' + sample + mn_output_suffix + '_mn.graphml'
        species_output_path = sample_dir + '/' + sample + '_species.json'
        taxon_info_output_path = sample_dir + '/' + sample + '_taxon_info.json'
        treemap_chemo_counted_results_path = sample_dir + '/' + sample + '_treemap_chemo_counted.html'
        treemap_chemo_intensity_results_path = sample_dir + '/' + sample + '_treemap_chemo_intensity.html'

        # If all file are already present, skip to the next folder
        # Else, if a file is missing, recompute everything. Could be adapted on a file per file basis 
        
        file_names_list = [isdb_results_path, mn_ci_ouput_path, repond_table_path,
                           repond_table_flat_path, mn_graphml_ouput_path, species_output_path,
                           taxon_info_output_path, treemap_chemo_counted_results_path, treemap_chemo_intensity_results_path
                           ]

        if all(list(map(os.path.isfile,file_names_list))):
            print('''
        Apparently everything is there, skipping file : ''' + sample
        )
            continue
        else:
                
            print('''
            Proceeding to spectral matching...
            ''')

            spectrums_query = list(load_from_mgf(spectra_file_path))
            print('%s spectra were found in the query file.' % len(spectrums_query))

            with nostdout():
                spectrums_query = [metadata_processing(s) for s in spectrums_query]
                spectrums_query = [peak_processing(s) for s in spectrums_query]
            similarity_score = PrecursorMzMatch(tolerance=float(parent_mz_tol), tolerance_type="Dalton")
            chunks_query = [spectrums_query[x:x+1000] for x in range(0, len(spectrums_query), 1000)]

            for chunk in chunks_query:
                scores = calculate_scores(chunk, spectrums_db_cleaned, similarity_score)
                indices = np.where(np.asarray(scores.scores))
                idx_row, idx_col = indices
                scans_id_map = {}
                i = 0
                for s in chunk:
                    scans_id_map[i] = int(s.metadata['scans'])
                    i += 1
                if match_score == 'modifiedcosine':
                    score = ModifiedCosine(tolerance=float(msms_mz_tol))
                elif match_score == 'cosinegreedy':
                    score = CosineGreedy(tolerance=float(msms_mz_tol))
                elif match_score == 'ms2deepscore':
                    model = load_model(model_path)
                    score = MS2DeepScore(model)            
                data = []
                for (x,y) in tzip(idx_row,idx_col):
                    if x<y:
                        if (match_score == 'cosinegreedy') | (match_score == 'modifiedcosine'):
                            msms_score, n_matches = score.pair(chunk[x], spectrums_db_cleaned[y])[()]
                            if (msms_score>float(min_score)) & (n_matches>int(min_peaks)):
                                feature_id = scans_id_map[x]
                                data.append({'msms_score':msms_score,
                                            'matched_peaks':n_matches,
                                            'feature_id': feature_id,
                                            'reference_id':y + 1,
                                            'inchikey': spectrums_db_cleaned[y].get("name")})
                        elif match_score == 'ms2deepscore':
                            msms_score = score.pair(chunk[x], spectrums_db_cleaned[y])                        
                            if msms_score>float(min_score):
                                feature_id = scans_id_map[x]
                                data.append({'msms_score':msms_score,
                                            'feature_id': feature_id,
                                            'reference_id':y + 1,
                                            'inchikey': spectrums_db_cleaned[y].get("name")})
                df = pd.DataFrame(data)
                df.to_csv(isdb_results_path, mode='a', header=not os.path.exists(isdb_results_path), sep = '\t')

            print('''
            Spectral matching done!
            ''')

            print('''
            Proceeding to Molecular Networking...
            ''')      
            if mn_score == 'modifiedcosine':
                score = ModifiedCosine(tolerance=float(msms_mz_tol))
            elif mn_score == 'cosinegreedy':
                score = CosineGreedy(tolerance=float(msms_mz_tol))
            elif mn_score == 'ms2deepscore':
                model = load_model(mn_model_path)
                score = MS2DeepScore(model)

            scores = calculate_scores(spectrums_query, spectrums_query, score, is_symmetric=True)
            ms_network = SimilarityNetwork(identifier_key="scans", score_cutoff = mn_score_cutoff, top_n = mn_top_n, max_links = mn_max_links, link_method = 'mutual')
            ms_network.create_network(scores)
            ms_network.export_to_graphml(mn_graphml_ouput_path)
            components = connected_component_subgraphs(ms_network.graph)

            comp_dict = {idx: comp.nodes() for idx, comp in enumerate(components)}
            attr = {n: {'component_id' : comp_id} for comp_id, nodes in comp_dict.items() for n in nodes}
            comp = pd.DataFrame.from_dict(attr, orient = 'index')
            comp.reset_index(inplace = True)
            comp.rename(columns={'index': 'feature_id'}, inplace=True)
            count = comp.groupby('component_id').count()
            count['new_ci'] = np.where(count['feature_id'] > 1, count.index, -1)
            new_ci = pd.Series(count.new_ci.values,index=count.index).to_dict()
            comp['component_id'] = comp['component_id'].map(new_ci)
            spectrums_query_metadata_df = pd.DataFrame(s.metadata for s in spectrums_query)
            comp = comp.merge(spectrums_query_metadata_df[['feature_id', 'precursor_mz']], how='left')
            comp.to_csv(mn_ci_ouput_path, sep = '\t', index = False)

            print('''
            Molecular Networking done !
            ''')

            dt_isdb_results = pd.read_csv(isdb_results_path,
                                        sep='\t',
                                        usecols=['msms_score', 'feature_id', 'reference_id', 'inchikey'],
                                        on_bad_lines='skip', low_memory=True)

            dt_isdb_results['libname'] = 'ISDB'

            dt_isdb_results.rename(columns={
                'inchikey': 'short_inchikey',
                'msms_score': 'score_input'}, inplace=True)

            clusterinfo_summary = pd.read_csv(mn_ci_ouput_path,
                                            sep='\t',
                                            usecols=['feature_id', 'precursor_mz', 'component_id'],
                                            on_bad_lines='skip', low_memory=True)

            clusterinfo_summary.rename(columns={'precursor_mz': 'mz'}, inplace=True)

            cluster_count = clusterinfo_summary.drop_duplicates(
                subset=['feature_id', 'component_id']).groupby("component_id").count()
            cluster_count = cluster_count[['feature_id']].rename(
                columns={'feature_id': 'ci_count'}).reset_index()

            # ## we now merge this back with the isdb matched results 
            dt_isdb_results = pd.merge(dt_isdb_results, clusterinfo_summary, on='feature_id')

            db_metadata = pd.read_csv(metadata_path,
                                    sep=',', on_bad_lines='skip', low_memory=False)

            db_metadata['short_inchikey'] = db_metadata.structure_inchikey.str.split(
                "-", expand=True)[0]
            db_metadata.reset_index(inplace=True)

            print('Number of features: ' + str(len(clusterinfo_summary)))
            print('Number of MS2 annotation: ' + str(len(dt_isdb_results)))

            # Now we directly do the MS1 matching stage on the cluster_summary. No need to have MS2 annotations

            print('''
            Proceeding to MS1 annotation ...
            ''')
            super_df = []

            for i, row in tqdm(clusterinfo_summary.iterrows(), total=clusterinfo_summary.shape[0]):
                par_mass = clusterinfo_summary.loc[i, 'mz']
                df_0 = clusterinfo_summary.loc[[i], ['feature_id', 'mz', 'component_id']]
                df_1 = adducts_df[(adducts_df['min'] <= par_mass) & (adducts_df['max'] >= par_mass)]
                df_1['key'] = i
                df_1.drop(['min', 'max'], axis=1, inplace=True)
                df_tot = pd.merge(df_0, df_1, left_index=True, right_on='key', how='left')
                super_df.append(df_tot)

            df_MS1 = pd.concat(super_df, axis=0)
            del super_df

            df_MS1 = df_MS1.drop(['key'], axis=1).drop_duplicates(
                subset=['feature_id', 'adduct'])

            df_MS1['libname'] = 'MS1_match'

            print('''
            MS1 annotation done !
            ''')

            df_meta_2 = db_metadata[['short_inchikey', 'structure_exact_mass']]
            df_meta_2 = df_meta_2.dropna(subset=['structure_exact_mass'])
            df_meta_2 = df_meta_2.drop_duplicates(
                subset=['short_inchikey', 'structure_exact_mass'])

            df_meta_2 = df_meta_2.round({'structure_exact_mass': 5})
            df_MS1 = df_MS1.round({'exact_mass': 5})

            df_MS1_merge = pd.merge(df_MS1, df_meta_2, left_on='exact_mass',
                                    right_on='structure_exact_mass', how='left')
            df_MS1_merge = df_MS1_merge.dropna(subset=['short_inchikey'])

            df_MS1_merge['match_mzerror_MS1'] = df_MS1_merge['mz'] - \
                df_MS1_merge['adduct_mass']
            df_MS1_merge = df_MS1_merge.round({'match_mzerror_MS1': 5}).astype({
                'match_mzerror_MS1': 'str'})

            df_MS1_merge = df_MS1_merge.drop(
                ['structure_exact_mass', 'adduct_mass', 'exact_mass'], axis=1)
            df_MS1_merge['score_input'] = 0

            # Merge MS1 results with MS2 annotations
            dt_isdb_results = pd.concat([dt_isdb_results, df_MS1_merge])

            print('Number of annotated features after MS1: ' +
                str(len(df_MS1_merge['feature_id'].unique())))

            print('Total number of MS1 and MSMS annotations: ' + str(len(dt_isdb_results)))

            # Rank annotations based on the spectral score

            dt_isdb_results["score_input"] = pd.to_numeric(
                dt_isdb_results["score_input"], downcast="float")
            dt_isdb_results['rank_spec'] = dt_isdb_results[['feature_id', 'score_input']].groupby(
                'feature_id')['score_input'].rank(method='dense', ascending=False)

            dt_isdb_results.reset_index(inplace=True, drop=True)

            # now we merge with the Occurences DB metadata after selection of our columns of interest

            cols_to_use = ['structure_smiles_2D', 'structure_molecular_formula',
                        'structure_exact_mass', 'short_inchikey', 'structure_taxonomy_npclassifier_01pathway', 
                        'structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class',
                        'organism_name', 'organism_taxonomy_ottid', 'organism_taxonomy_01domain', 'organism_taxonomy_02kingdom', 'organism_taxonomy_03phylum',
                        'organism_taxonomy_04class', 'organism_taxonomy_05order', 'organism_taxonomy_06family', 'organism_taxonomy_08genus',
                        'organism_taxonomy_09species', 'organism_taxonomy_10varietas' ]

            dt_isdb_results = pd.merge(
                left=dt_isdb_results, right=db_metadata[cols_to_use], left_on='short_inchikey', right_on='short_inchikey', how='outer')
            dt_isdb_results.dropna(subset=['feature_id'], inplace=True)

            print('Total number of annotations with unique Biosource/line: ' +
                str(len(dt_isdb_results)))


            # Now we want to get the taxonomic information for each of the samples
            # so we want to extract the species information from the metadata file
            samples_metadata[organism_header].dropna(inplace = True)
            samples_metadata[organism_header] = samples_metadata[organism_header].str.lower()
            species = samples_metadata[organism_header].unique()
            len_species = len(species)

            print("%s unique species have been selected from the metadata table." % len_species )

            species_tnrs_matched = OT.tnrs_match(species, context_name=None, do_approximate_matching=True, include_suppressed=False)

            with open(str(species_output_path), 'w') as out:
                sf = json.dumps(species_tnrs_matched.response_dict, indent=2, sort_keys=True)
                out.write('{}\n'.format(sf))

            with open(str(species_output_path)) as tmpfile:
                    jsondic = json.loads(tmpfile.read())

            json_normalize(jsondic)

            df_species_tnrs_matched = json_normalize(jsondic,
                        record_path=['results', 'matches']
                        )

            # We then want to match with the accepted name instead of the synonym in case both are present. 
            # We thus order by matched_name and then by is_synonym status prior to returning the first row.
            if len(df_species_tnrs_matched) != 0:
                df_species_tnrs_matched.sort_values(['search_string', 'is_synonym'], axis = 0, inplace = True)
                df_species_tnrs_matched_unique = df_species_tnrs_matched.drop_duplicates('search_string', keep = 'first')

                # both df are finally merged
                merged_df = pd.merge(samples_metadata, df_species_tnrs_matched_unique, how='left', left_on=organism_header, right_on='search_string', indicator=True)

                # converting 'ott_ids' from float to int (check the astype('Int64') whic will work while the astype('int') won't see https://stackoverflow.com/a/54194908)
                merged_df['taxon.ott_id'] = merged_df['taxon.ott_id'].astype('Int64')

                # However, we then need to put them back to 
                merged_df['taxon.ott_id']
                ott_list = list(merged_df['taxon.ott_id'].dropna().astype('int'))

                taxon_info = []

                for i in ott_list:
                    query = OT.taxon_info(i, include_lineage=True)
                    taxon_info.append(query)

                tl = []

                for i in taxon_info:
                    with open(str(taxon_info_output_path), 'w') as out:
                        tl.append(i.response_dict)
                        yo = json.dumps(tl)
                        out.write('{}\n'.format(yo))

                with open(str(taxon_info_output_path)) as tmpfile:
                    jsondic = json.loads(tmpfile.read())

                df = json_normalize(jsondic)

                df_tax_lineage = json_normalize(jsondic,
                            record_path=['lineage'],
                            meta = ['ott_id', 'unique_name'],
                            record_prefix='sub_',
                            errors='ignore'
                            )

                # This keeps the last occurence of each ott_id / sub_rank grouping https://stackoverflow.com/a/41886945
                df_tax_lineage_filtered = df_tax_lineage.groupby(['ott_id', 'sub_rank'], as_index=False).last()

                #Here we pivot long to wide to get the taxonomy
                df_tax_lineage_filtered_flat = df_tax_lineage_filtered.pivot(index='ott_id', columns='sub_rank', values='sub_name')

                # Here we actually also want the lowertaxon (species usually) name
                df_tax_lineage_filtered_flat = pd.merge(df_tax_lineage_filtered_flat, df_tax_lineage_filtered[['ott_id', 'unique_name']], how='left', on='ott_id', )

                #Despite the left join ott_id are duplicated 
                df_tax_lineage_filtered_flat.drop_duplicates(subset = ['ott_id', 'unique_name'], inplace = True)

                # here we want to have these columns whatevere happens
                col_list = ['ott_id', 'domain', 'kingdom', 'phylum',
                                        'class', 'order', 'family', 'genus', 'unique_name']

                df_tax_lineage_filtered_flat = df_tax_lineage_filtered_flat.reindex(columns=col_list, fill_value = np.NaN)

                # We now rename our columns of interest
                renaming_dict = {'domain': 'query_otol_domain',
                            'kingdom': 'query_otol_kingdom',
                            'phylum': 'query_otol_phylum',
                            'class': 'query_otol_class',
                            'order': 'query_otol_order',
                            'family': 'query_otol_family',
                            'genus': 'query_otol_genus',
                            'unique_name': 'query_otol_species'}

                df_tax_lineage_filtered_flat.rename(columns=renaming_dict, inplace=True)

                # We select columns of interest 
                cols_to_keep = ['ott_id',
                            'query_otol_domain',
                            'query_otol_kingdom',
                            'query_otol_phylum',
                            'query_otol_class',
                            'query_otol_order',
                            'query_otol_family',
                            'query_otol_genus',
                            'query_otol_species']

                df_tax_lineage_filtered_flat = df_tax_lineage_filtered_flat[cols_to_keep]

                # We merge this back with the samplemetadata only if we have an ott.id in the merged df 
                samples_metadata = pd.merge(merged_df[pd.notnull(merged_df['taxon.ott_id'])], df_tax_lineage_filtered_flat, how='left', left_on='taxon.ott_id', right_on='ott_id' )

                # Here we will add three columns (even for the simple repond this way it will be close to the multiple species repond)
                # these line will need to be defined as function arguments
                cols_att = ['query_otol_domain', 'query_otol_kingdom', 'query_otol_phylum', 'query_otol_class',
                            'query_otol_order', 'query_otol_family', 'query_otol_genus', 'query_otol_species']
                for col in cols_att:
                    dt_isdb_results[col] = samples_metadata[col][0]
            else:
                cols_att = ['query_otol_domain', 'query_otol_kingdom', 'query_otol_phylum', 'query_otol_class',
                            'query_otol_order', 'query_otol_family', 'query_otol_genus', 'query_otol_species']
                for col in cols_att:
                    dt_isdb_results[col] = 'no_species_matched_from_metadata'

            print('''
            Proceeding to taxonomically informed reponderation ...
            ''')

            cols_ref = ['organism_taxonomy_01domain', 'organism_taxonomy_02kingdom',  'organism_taxonomy_03phylum', 'organism_taxonomy_04class',
                        'organism_taxonomy_05order', 'organism_taxonomy_06family','organism_taxonomy_08genus', 'organism_taxonomy_09species']

            cols_match = ['matched_domain', 'matched_kingdom', 'matched_phylum', 'matched_class',
                        'matched_order', 'matched_family', 'matched_genus', 'matched_species']

            col_prev = None
            for col_ref, col_att, col_match in zip(cols_ref, cols_att, cols_match):
                    dt_isdb_results[col_ref].fillna('unknown', inplace=True)
                    dt_isdb_results[col_att].fillna('unknown', inplace=True)
                    dt_isdb_results[col_ref] = dt_isdb_results[col_ref].apply(lambda x: [x])
                    dt_isdb_results[col_att] = dt_isdb_results[col_att].apply(lambda x: [x])
                    dt_isdb_results[col_match] = [list(set(a).intersection(set(b))) for a, b in zip(dt_isdb_results[col_ref], dt_isdb_results[col_att])] # Allows to compare 2 lists
                    dt_isdb_results[col_match] = dt_isdb_results[col_match].apply(lambda y: np.nan if len(y)==0 else y)
                    if col_prev != None:
                            dt_isdb_results[col_match].where(dt_isdb_results[col_prev].notnull(), np.nan)
                    col_prev = col_match

            dt_isdb_results['score_taxo'] = dt_isdb_results[cols_match].count(axis=1)

            # Filter out MS1 annotations without a reweighting at the family level at least

            dt_isdb_results = dt_isdb_results[
                (dt_isdb_results['score_taxo'] >= min_score_taxo_ms1) | (
                dt_isdb_results['libname'] == 'ISDB')]


            # print('Total number of annotations after filtering MS1 annotations not reweighted at taxonomical level min: ' +
            #     str(len(dt_isdb_results)))

            print('Number of annotations reweighted at the domain level: ' +
                str(dt_isdb_results['matched_domain'].count()))
            print('Number of annotations reweighted at the kingom level: ' +
                str(dt_isdb_results['matched_kingdom'].count()))
            print('Number of annotations reweighted at the phylum level: ' +
                str(dt_isdb_results['matched_phylum'].count()))
            print('Number of annotations reweighted at the class level: ' +
                str(dt_isdb_results['matched_class'].count()))
            print('Number of annotations reweighted at the order level: ' +
                str(dt_isdb_results['matched_order'].count()))
            print('Number of annotations reweighted at the family level: ' +
                str(dt_isdb_results['matched_family'].count()))
            print('Number of annotations reweighted at the genus level: ' +
                str(dt_isdb_results['matched_genus'].count()))
            print('Number of annotations reweighted at the species level: ' +
                str(dt_isdb_results['matched_species'].count()))


            # we set the spectral score column as float
            dt_isdb_results["score_input"] = pd.to_numeric(
                dt_isdb_results["score_input"], downcast="float")
            # and we add it to the max taxo score :
            dt_isdb_results['score_input_taxo'] = dt_isdb_results['score_taxo'] + \
                dt_isdb_results['score_input']


            dt_isdb_results['rank_spec_taxo'] = dt_isdb_results.groupby(
                'feature_id')['score_input_taxo'].rank(method='dense', ascending=False)

            dt_isdb_results = dt_isdb_results.groupby(["feature_id"]).apply(
                lambda x: x.sort_values(["rank_spec_taxo"], ascending=True)).reset_index(drop=True)

            # Get cluster Chemical class
            for col in ['structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class']:

                df = dt_isdb_results.copy()
                df = df.drop_duplicates(subset=['feature_id', col])
                df = df[df["component_id"] != -1]
                df = df[df.rank_spec_taxo <= top_N_chemical_consistency]
                df = df.groupby(
                    ["component_id", col]
                ).agg({'feature_id': 'count',
                    'rank_spec_taxo': 'mean'}
                    ).reset_index(
                ).rename(columns={'feature_id': (col + '_count'),
                                'rank_spec_taxo': ('rank_' + col + '_mean')}
                        ).merge(cluster_count, on='component_id', how='left')

                df[('freq_' + col)] = df[(col + '_count')] / df['ci_count']
                df[(col + '_score')] = df[('freq_' + col)] / \
                    (df[('rank_' + col + '_mean')]**(0.5))
                df = df.sort_values(
                    (col + '_score'), ascending=False
                ).drop_duplicates(['component_id']
                                ).rename(columns={col: (col + '_consensus')})
                dt_isdb_results = dt_isdb_results.merge(
                    df[[(col + '_consensus'), ('freq_' + col), 'component_id']], on='component_id', how='left')

            # Chemical consistency reweighting

            print('''
            Proceeding to chemically informed reponderation ...
            ''')

            dt_isdb_results['structure_taxonomy_npclassifier_01pathway_score'] = dt_isdb_results.apply(
                lambda x: 1 if x.structure_taxonomy_npclassifier_01pathway == x.structure_taxonomy_npclassifier_01pathway_consensus else 0, axis=1)
            dt_isdb_results['structure_taxonomy_npclassifier_02superclass_score'] = dt_isdb_results.apply(
                lambda x: 2 if x.structure_taxonomy_npclassifier_02superclass == x.structure_taxonomy_npclassifier_02superclass_consensus else 0, axis=1)
            dt_isdb_results['structure_taxonomy_npclassifier_03class_score'] = dt_isdb_results.apply(
                lambda x: 3 if x.structure_taxonomy_npclassifier_03class == x.structure_taxonomy_npclassifier_03class_consensus else 0, axis=1)

            dt_isdb_results['score_max_consistency'] = dt_isdb_results[[
                "structure_taxonomy_npclassifier_01pathway_score",
                "structure_taxonomy_npclassifier_02superclass_score",
                "structure_taxonomy_npclassifier_03class_score"
            ]].max(axis=1)


            dt_isdb_results['final_score'] = dt_isdb_results['score_input'] + dt_isdb_results['score_taxo'] + dt_isdb_results['score_max_consistency']

            dt_isdb_results['rank_final'] = dt_isdb_results.groupby(
                'feature_id')['final_score'].rank(method='dense', ascending=False)



            # print('Number of annotations reweighted at the NPClassifier pathway level: ' +
            #     str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_01pathway_score'] == 1)])))
            # print('Number of annotations reweighted at the NPClassifier superclass level: ' +
            #     str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_02superclass_score'] == 2)])))
            # print('Number of annotations reweighted at the NPClassifier class level: ' +
            #     str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_03class_score'] == 3)])))

            
            # dt_isdb_results_chem_rew = dt_isdb_results_chem_rew[
            #     (dt_isdb_results_chem_rew['score_max_consistency'] >= min_score_chemo_ms1) | (dt_isdb_results_chem_rew['libname'] == 'ISDB')
            #     ]


            dt_isdb_results_chem_rew = dt_isdb_results.loc[(
                dt_isdb_results.rank_final <= int(top_to_output))]
            dt_isdb_results_chem_rew[["feature_id", "rank_final", "component_id"]] = dt_isdb_results_chem_rew[[
                "feature_id", "rank_final", "component_id"]].apply(pd.to_numeric, downcast='signed', axis=1)
            dt_isdb_results_chem_rew = dt_isdb_results_chem_rew.sort_values(
                ["feature_id", "rank_final"], ascending=(False, True))
            dt_isdb_results_chem_rew = dt_isdb_results_chem_rew.astype(str)


            # Here we would like to filter results when short IK are repeated for the same feature_id at the same final rank
            # see issue (https://gitlab.com/tima5/taxoscorer/-/issues/23)

            dt_isdb_results_chem_rew = dt_isdb_results_chem_rew.drop_duplicates(subset=['feature_id', 'short_inchikey'], keep='first')

            dt_isdb_results_chem_rew = dt_isdb_results_chem_rew.astype({'feature_id' : 'int64'})
        
            dt_isdb_results_chem_rew['lowest_matched_taxon'] = dt_isdb_results_chem_rew['matched_species']
            dt_isdb_results_chem_rew['lowest_matched_taxon'] = dt_isdb_results_chem_rew['lowest_matched_taxon'].replace('nan', np.NaN)
            col_matched = ['matched_genus', 'matched_family', 'matched_order', 'matched_order', 'matched_phylum', 'matched_kingdom', 'matched_domain']
            for col in col_matched:
                dt_isdb_results_chem_rew[col] = dt_isdb_results_chem_rew[col].replace('nan', np.NaN)  
                dt_isdb_results_chem_rew['lowest_matched_taxon'].fillna(dt_isdb_results_chem_rew[col], inplace=True)

            annot_attr = ['rank_spec', 'score_input', 'libname', 'short_inchikey', 'structure_smiles_2D', 'structure_molecular_formula', 'adduct',
                        'structure_exact_mass', 'structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class',
                        'query_otol_species', 'lowest_matched_taxon', 'score_taxo', 'score_max_consistency', 'final_score', 'rank_final']

            comp_attr = ['component_id', 'structure_taxonomy_npclassifier_01pathway_consensus', 'freq_structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass_consensus',
                        'freq_structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class_consensus', 'freq_structure_taxonomy_npclassifier_03class']


            col_to_keep = ['feature_id'] + comp_attr + annot_attr

            df4cyto_flat = dt_isdb_results_chem_rew[col_to_keep]

            all_columns = list(df4cyto_flat) # Creates list of all column headers
            df4cyto_flat[all_columns] = df4cyto_flat[all_columns].astype(str)

            gb_spec = {c: '|'.join for c in annot_attr}
            for c in comp_attr:
                gb_spec[c] = 'first'

            df4cyto = df4cyto_flat.groupby('feature_id').agg(gb_spec)

            df4cyto_flat.to_csv(repond_table_flat_path, sep='\t')

            df4cyto.to_csv(repond_table_path, sep='\t')
            
                            
            # %%
            ######################################################################################################
            ######################################################################################################
            # Preparing tables for plots
            ######################################################################################################
            # Loading clean tables
            #feature_table.reset_index(inplace=True)

            feature_intensity_table_formatted = feature_intensity_table_formatter(feature_intensity_table=feature_table,
                                                                                file_extension='.mzML',
                                                                                msfile_suffix=' Peak area')
            
            dt_samples_metadata = samples_metadata_loader_simple(
                samples_metadata_table_path=metadata_sample_path,
                organism_header=organism_header)


            table_for_plots_formatted = table_for_plots_formatter(df_flat=df4cyto_flat,
                                                                feature_intensity_table_formatted=feature_intensity_table_formatted,
                                                                dt_samples_metadata=samples_metadata,
                                                                organism_header=organism_header,
                                                                sampletype_header=sampletype_header,
                                                                multi_plot=False)

            # %%
            ######################################################################################################
            ######################################################################################################
            # Plotting figures
            ######################################################################################################
            # Single parameters

            plotter_single(dt_isdb_results_int=table_for_plots_formatted,
                        dt_samples_metadata=samples_metadata,
                        organism_header=organism_header,
                        treemap_chemo_counted_results_path=treemap_chemo_counted_results_path,
                        treemap_chemo_intensity_results_path=treemap_chemo_intensity_results_path)


print('Finished in %s seconds.' % (time.time() - start_time))
