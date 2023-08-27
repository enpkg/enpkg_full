import pandas as pd

def feature_intensity_table_formatter(feature_intensity_table):

    """Formats a feature intensity table to an appropriate format for biosource_contribution_fetcher()
    
    Args:
        feature_intensity_table (dataframe): an MzMine feature intensity table
        
    Returns:
        dataframe: a formatted MzMine feature intensity table
    """
    # The feature_intensity_table is loaded

    # formatting the feature table 
    feature_intensity_table.rename(columns={'row ID': 'row_ID'}, inplace=True)
    feature_intensity_table.set_index('row_ID', inplace=True)
    feature_intensity_table = feature_intensity_table.filter(regex='Peak area')
    feature_intensity_table.rename(columns={'precursor_mz': 'mz'}, inplace=True)
    feature_intensity_table.columns = feature_intensity_table.columns.str.replace(' Peak area', '') 
    feature_intensity_table.rename_axis("MS_filename", axis="columns", inplace = True)
    feature_intensity_table = feature_intensity_table.rename(columns= {feature_intensity_table.columns[0]:'intensity'} )
    return feature_intensity_table

