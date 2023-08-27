import pandas as pd
import numpy as np

def cluster_counter(clusterinfo_summary_file):
    """Count the numbers of nodes per component index in a molecular network

    Args:
        clusterinfo_summary_file (DataFrame) : A molecular network clusterinfo_summary_file

    Returns:
        cluster_count (DataFrame): A DataFrame with the number of nodes per component index
    """    
    
    cluster_count = clusterinfo_summary_file.drop_duplicates(
        subset=['feature_id', 'component_id']).groupby("component_id").count()
    cluster_count = cluster_count[['feature_id']].rename(
        columns={'feature_id': 'ci_count'}).reset_index()
    return cluster_count


def top_N_slicer(input_df, top_to_output):

    """ Keeps only the top N candidates out of an annotation table and sorts them by rank

    Args:
        input_df (DataFrame) : A DataFrame of candidates annotations
        top_to_output (int): Top N candidate annotations to keep
        
    Returns:
        output_df (DataFrame): a DataFrame with the top N annotation ordered by final rank
    """

    output_df = input_df.loc[(
        input_df.rank_final <= int(top_to_output))]
    output_df[["feature_id", "rank_final", "component_id"]] = output_df[[
        "feature_id", "rank_final", "component_id"]].apply(pd.to_numeric, downcast='signed', axis=1)
    output_df = output_df.sort_values(
        ["feature_id", "rank_final"], ascending=(False, True))

    return output_df


def annotation_table_formatter_taxo(input_df, min_score_taxo_ms1, min_score_chemo_ms1):
    """ A bunche of formatter frunctions for output

    Args:
        input_df (DataFrame) : A DataFrame of annotations
        min_score_taxo_ms1 (int): Minimal taxonomical score for MS1 annotations
        min_score_chemo_ms1 (int): Minimal cluster chemical consistency score for MS1 annotations
    Returns:
        dt_output_flat (DataFrame): A flat DataFrame one annotation by line
        dt_output_cyto (DataFrame): A Cytoscape compatible DataFrame with one feature by line (sep = |)
    """

    # Here we would like to filter results when short IK are repeated for the same feature_id at the same final rank

    input_df = input_df.drop_duplicates(
        subset=['feature_id', 'short_inchikey'], keep='first')

    input_df = input_df.astype(
        {'feature_id': 'int64'})

    input_df['lowest_matched_taxon'] = input_df['matched_species']
    input_df['lowest_matched_taxon'] = input_df['lowest_matched_taxon'].replace(
        'nan', np.NaN)
    col_matched = ['matched_genus', 'matched_family', 'matched_order',
                    'matched_order', 'matched_phylum', 'matched_kingdom', 'matched_domain']
    for col in col_matched:
        input_df[col] = input_df[col].replace(
            'nan', np.NaN)
        input_df['lowest_matched_taxon'].fillna(
            input_df[col], inplace=True)

    annot_attr = ['rank_spec', 'score_input', 'libname', 'short_inchikey', 'structure_smiles_2D', 'structure_molecular_formula', 'adduct',
                    'structure_exact_mass', 'structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass',
                    'structure_taxonomy_npclassifier_03class',
                    'query_otol_species', 'lowest_matched_taxon', 'score_taxo', 'score_max_consistency', 'final_score', 'rank_final']

    comp_attr = ['component_id', 'structure_taxonomy_npclassifier_01pathway_consensus', 'freq_structure_taxonomy_npclassifier_01pathway',
                 'structure_taxonomy_npclassifier_02superclass_consensus',
                 'freq_structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class_consensus', 'freq_structure_taxonomy_npclassifier_03class']

    col_to_keep = ['feature_id'] + comp_attr + annot_attr

    # We add the min chemo score filter at this step
    input_df = input_df[
        ((input_df['score_taxo'] >= min_score_taxo_ms1) & (input_df['score_max_consistency'] >= min_score_chemo_ms1)) | (
            input_df['libname'] == 'ISDB')]
    dt_output_flat = input_df[col_to_keep]

    # Cytoscape formatting 

    all_columns = list(input_df) # Creates list of all column headers   
    input_df[all_columns] = input_df[all_columns].astype(str)
    gb_spec = {c: '|'.join for c in annot_attr}

    for c in comp_attr:
        gb_spec[c] = 'first'

    dt_output_cyto = input_df.groupby('feature_id').agg(gb_spec)
    dt_output_cyto.reset_index(inplace=True)

    return dt_output_flat, dt_output_cyto


def annotation_table_formatter_no_taxo(input_df, min_score_taxo_ms1, min_score_chemo_ms1):
    """ A bunche of formatter frunctions for output

    Args:
        input_df (DataFrame) : A DataFrame of annotations
        min_score_taxo_ms1 (int): Minimal taxonomical score for MS1 annotations
        min_score_chemo_ms1 (int): Minimal cluster chemical consistency score for MS1 annotations
    Returns:
        dt_output_flat (DataFrame): A flat DataFrame one annotation by line
        dt_output_cyto (DataFrame): A Cytoscape compatible DataFrame with one feature by line (sep = |)
    """

    # Here we would like to filter results when short IK are repeated for the same feature_id at the same final rank

    input_df = input_df.drop_duplicates(
        subset=['feature_id', 'short_inchikey'], keep='first')

    input_df = input_df.astype(
        {'feature_id': 'int64'})
    
    annot_attr = ['rank_spec', 'score_input', 'libname', 'short_inchikey', 'structure_smiles_2D', 'structure_molecular_formula', 'adduct',
                    'structure_exact_mass', 'structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass',
                    'structure_taxonomy_npclassifier_03class', 'score_taxo', 'score_max_consistency', 'final_score', 'rank_final']

    comp_attr = ['component_id', 'structure_taxonomy_npclassifier_01pathway_consensus', 'freq_structure_taxonomy_npclassifier_01pathway',
                 'structure_taxonomy_npclassifier_02superclass_consensus',
                 'freq_structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class_consensus', 'freq_structure_taxonomy_npclassifier_03class']

    col_to_keep = ['feature_id'] + comp_attr + annot_attr

    # We add the min chemo score filter at this step
    input_df = input_df[
        ((input_df['score_taxo'] >= min_score_taxo_ms1) & (input_df['score_max_consistency'] >= min_score_chemo_ms1)) | (
            input_df['libname'] == 'ISDB')]
    dt_output_flat = input_df[col_to_keep]

    # Cytoscape formatting 

    all_columns = list(input_df) # Creates list of all column headers   
    input_df[all_columns] = input_df[all_columns].astype(str)
    gb_spec = {c: '|'.join for c in annot_attr}

    for c in comp_attr:
        gb_spec[c] = 'first'

    dt_output_cyto = input_df.groupby('feature_id').agg(gb_spec)
    dt_output_cyto.reset_index(inplace=True)

    return dt_output_flat, dt_output_cyto


