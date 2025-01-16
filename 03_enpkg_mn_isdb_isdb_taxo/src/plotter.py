import numpy as np
import plotly.express as px

def plotter_count(df_input, sample_dir, organism, treemap_chemo_counted_results_path):
    """Plot a NPClassifer treemap from annotation table using the annotation count

    Args:
        df_input (DataFrame): An annotation table
        treemap_chemo_counted_results_path (str): Path to save the generated treemap
    """
    df_input = df_input.replace({np.nan:'None'})
    fig = px.treemap(df_input, path=['structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class'],
                     color='structure_taxonomy_npclassifier_01pathway',
                     color_discrete_map={
                         'Terpenoids':'#E76F51',
                         'Alkaloids': '#264653',
                         'Amino acids and Peptides': '#287271',
                         'Polyketides': '#2A9D8F',
                         'Shikimates and Phenylpropanoids': '#E9C46A',
                         'Fatty acids': '#8AB17D',
                         'Carbohydrates': '#F4A261',})
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25),
    title_text= sample_dir + " ("  +  organism + ") " + "- metabolite annotation overview (size proportional to number of annotations)")
    fig.update_annotations(font_size=12)
    fig.write_html(treemap_chemo_counted_results_path)


def plotter_intensity(df_input, feature_table, sample_dir, organism, treemap_chemo_intensity_results_path):
    """Plot a NPClassifer treemap from annotation table using the annotation average intensity

    Args:
        df_input (DataFrame): An annotation table
        feature_table (DataFrame): A formatted MzMine feature table
        treemap_chemo_intensity_results_path (str): Path to save the generated treemap
    """
    df_input = df_input.replace({np.nan:'None'})
    df_input = df_input.merge(feature_table, left_on = 'feature_id', right_index=True, how='left')
    fig = px.treemap(df_input, path=['structure_taxonomy_npclassifier_01pathway', 'structure_taxonomy_npclassifier_02superclass', 'structure_taxonomy_npclassifier_03class'],
                     color='intensity',
                     color_continuous_scale='RdBu_r',)
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25),
    title_text= sample_dir + " ("  +  organism + ") " + "- metabolite annotation overview (size proportional to the average features intensities)")
    fig.update_annotations(font_size=12)
    fig.write_html(treemap_chemo_intensity_results_path)

