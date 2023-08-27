import pandas as pd
import numpy as np
from helpers import cluster_counter

def taxonomical_reponderator(dt_isdb_results, min_score_taxo_ms1):
    """Perform taxonomical consistency reweighting on a list of candidates annotations

    Args:
        dt_isdb_results (DataFrame): An annotation table
        min_score_taxo_ms1 (int): Minimal score of MS1 annotations 

    Returns:
        DataFrame: An annotation table
    """ 
    
    df = dt_isdb_results.copy()
    cols_ref = ['organism_taxonomy_01domain', 'organism_taxonomy_02kingdom',  'organism_taxonomy_03phylum', 'organism_taxonomy_04class',
                'organism_taxonomy_05order', 'organism_taxonomy_06family', 'organism_taxonomy_08genus', 'organism_taxonomy_09species']

    cols_att = ['query_otol_domain', 'query_otol_kingdom', 'query_otol_phylum', 'query_otol_class',
                'query_otol_order', 'query_otol_family', 'query_otol_genus', 'query_otol_species']

    cols_match = ['matched_domain', 'matched_kingdom', 'matched_phylum', 'matched_class',
                'matched_order', 'matched_family', 'matched_genus', 'matched_species']

    col_prev = None

    for col_ref, col_att, col_match in zip(cols_ref, cols_att, cols_match):
        df[col_ref].fillna('Unknown', inplace=True)
        df[col_ref] = df[col_ref].apply(lambda x: [x])
        df[col_att] = df[col_att].apply(lambda x: [x])
        df[col_match] = [list(set(a).intersection(set(b))) for a, b in zip(df[col_ref], df[col_att])] # Allows to compare 2 lists
        df[col_match] = df[col_match].apply(lambda y: np.nan if len(y)==0 else y)
        if col_prev != None:
            df[col_match].where(df[col_prev].notnull(), np.nan)
        col_prev = col_match

    # Note for future self. If you get a TypeError: unhashable type: 'list' error. before messing around with the previous line make sure that the taxonomy has been appended at the df = pd.merge(
    #  ' df, df_merged, left_on='feature_id', right_on='row_ID', how='left')' step before. Usuall this comes from a bad definition of the regex (ex .mzXMl insted of .mzML) in the params file. Should find a safer way to deal with these extensions in the header.

    df['score_taxo'] = df[cols_match].count(axis=1)

    # Filter out MS1 annotations without a reweighting at a given taxo level prior to chemo repond

    df = df.loc[(df['score_taxo'] >= min_score_taxo_ms1) | (df['libname'] == 'ISDB')]


    # we set the spectral score column as float
    df["score_input"] = pd.to_numeric(
        df["score_input"], downcast="float")
    # and we add it to the max txo score :
    df['score_input_taxo'] = df['score_taxo'] + df['score_input']

    df['rank_spec_taxo'] = df.groupby(
        'feature_id')['score_input_taxo'].rank(method='dense', ascending=False)

    df = df.groupby(["feature_id"]).apply(
        lambda x: x.sort_values(["rank_spec_taxo"], ascending=True)).reset_index(drop=True)
    
    print('Total number of annotations after filtering MS1 annotations not reweighted at the minimal taxonomical level: ' +
        str(len(df)))
    
    if len(df) != 0:
        print('Number of annotations reweighted at the domain level: ' +
            str(df['matched_domain'].count()))
        print('Number of annotations reweighted at the kingdom level: ' +
            str(df['matched_kingdom'].count()))
        print('Number of annotations reweighted at the phylum level: ' +
            str(df['matched_phylum'].count()))
        print('Number of annotations reweighted at the class level: ' +
            str(df['matched_class'].count()))
        print('Number of annotations reweighted at the order level: ' +
            str(df['matched_order'].count()))
        print('Number of annotations reweighted at the family level: ' +
            str(df['matched_family'].count()))
        print('Number of annotations reweighted at the genus level: ' +
            str(df['matched_genus'].count()))
        print('Number of annotations reweighted at the species level: ' +
            str(df['matched_species'].count()))

    return df



def chemical_reponderator(clusterinfo_summary_file, dt_isdb_results, top_N_chemical_consistency, msms_weight, taxo_weight, chemo_weight):
    """Perform chemical consistency reweighting on a list of candidates annotations
    
    Args:
        clusterinfo_summary_file (DataFrame): The MN metadata file
        dt_isdb_results (DataFrame): An annotation table
        top_N_chemical_consistency (int): Top N candidates to consider for cluster chemical consistency determination
        
    Returns:
        DataFrame: An annotation table
    """
    
    cluster_count = cluster_counter(clusterinfo_summary_file)
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

    dt_isdb_results['final_score'] = msms_weight * dt_isdb_results['score_input'] + \
        taxo_weight * dt_isdb_results['score_taxo'] + \
        chemo_weight * dt_isdb_results['score_max_consistency']

    dt_isdb_results['rank_final'] = dt_isdb_results.groupby(
        'feature_id')['final_score'].rank(method='dense', ascending=False)

    print('Number of annotations reweighted at the NPClassifier pathway level: ' +
          str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_01pathway_score'] == 1)])))
    print('Number of annotations reweighted at the NPClassifier superclass level: ' +
          str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_02superclass_score'] == 2)])))
    print('Number of annotations reweighted at the NPClassifier class level: ' +
          str(len(dt_isdb_results[(dt_isdb_results['structure_taxonomy_npclassifier_03class_score'] == 3)])))

    return dt_isdb_results



