import pandas as pd
from tqdm import tqdm

pd.options.mode.chained_assignment = None

def ms1_matcher(input_df, adducts_df, df_metadata):
    """Perform MS

    Args:
        input_df (DataFrame): Input table with features m/z
        adducts_df (DataFrame): Potential adducts m/z
        df_metadata (DataFrame): Potential adducts metadata

    Returns:
        DataFrame: An annotation table 
    """    

    super_df = []

    for i, _ in tqdm(input_df.iterrows(), total=input_df.shape[0]):
        par_mass = input_df.loc[i, 'mz']
        df_0 = input_df.loc[[i], [
            'feature_id', 'mz', 'component_id']]
        df_1 = adducts_df[(adducts_df['min'] <= par_mass) &
                          (adducts_df['max'] >= par_mass)]
        df_1['key'] = i
        df_1.drop(['min', 'max'], axis=1, inplace=True)
        df_tot = pd.merge(df_0, df_1, left_index=True,
                          right_on='key', how='left')
        super_df.append(df_tot)

    df_MS1 = pd.concat(super_df, axis=0)
    del super_df

    df_MS1 = df_MS1.drop(['key'], axis=1).drop_duplicates(
        subset=['feature_id', 'adduct'])

    df_MS1['libname'] = 'MS1_match'

    df_meta_short = df_metadata[['short_inchikey', 'structure_exact_mass']]
    df_meta_short = df_meta_short.dropna(subset=['structure_exact_mass'])
    df_meta_short = df_meta_short.drop_duplicates(
        subset=['short_inchikey', 'structure_exact_mass'])

    df_meta_short = df_meta_short.round({'structure_exact_mass': 5})
    df_MS1 = df_MS1.round({'exact_mass': 5})

    df_MS1_merge = pd.merge(df_MS1, df_meta_short, left_on='exact_mass',
                            right_on='structure_exact_mass', how='left')
    df_MS1_merge = df_MS1_merge.dropna(subset=['short_inchikey'])

    df_MS1_merge['match_mzerror_MS1'] = df_MS1_merge['mz'] - df_MS1_merge['adduct_mass']
    df_MS1_merge = df_MS1_merge.round({'match_mzerror_MS1': 5}).astype({
        'match_mzerror_MS1': 'str'})

    df_MS1_merge = df_MS1_merge.drop(
        ['structure_exact_mass', 'adduct_mass', 'exact_mass'], axis=1)
    df_MS1_merge['msms_score'] = 0

    return df_MS1_merge
