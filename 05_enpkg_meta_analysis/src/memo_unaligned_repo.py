import memo_ms as memo
import os
import datatable as dt
import pandas as pd
import numpy as np
from pathlib import Path
import yaml


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
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config


if __name__ == "__main__":
    # Set working directory
    p = Path(__file__).parents[1]
    os.chdir(p)

    # Load YAML configuration
    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
        exit()

    with open('../params/user.yml') as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Apply variable substitution
    params_list_full = substitute_variables(params_list_full)
    params_list = params_list_full['memo']

    # Access parameters
    sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
    ionization = params_list_full['general']['polarity']
    min_relative_intensity = params_list['min_relative_intensity']
    max_relative_intensity = params_list['max_relative_intensity']
    min_peaks_required = params_list['min_peaks_required']
    losses_from = params_list['losses_from']
    losses_to = params_list['losses_to']
    n_decimals = params_list['n_decimals']
    filter_blanks = params_list['filter_blanks']
    word_max_occ_blanks = params_list['word_max_occ_blanks']
    output = os.path.normpath(params_list['output'])
    output_path = os.path.normpath(params_list['output_path'])

    # Debug: Verify resolved paths
    print(f"Resolved output path: {output_path}")

    # Ensure output path is resolved correctly
    if "${" in output_path:
        raise ValueError("Output path contains unresolved variables. Check substitution logic.")

    # Determine patterns for ionization modes
    pattern_to_match2 = None
    if ionization == 'pos':
        pattern_to_match1 = '_features_ms2_pos.mgf'
    elif ionization == 'neg':
        pattern_to_match1 = '_features_ms2_neg.mgf'
    elif ionization == 'both':
        pattern_to_match1 = '_features_ms2_pos.mgf'
        pattern_to_match2 = '_features_ms2_neg.mgf'
    else:
        raise ValueError('Ionization must be pos, neg, or both')

    if not filter_blanks and word_max_occ_blanks != -1:
        raise ValueError('Set --filter_blanks to True to use word_max_occ_blanks')

    # Count files matching the pattern
    i = sum(
        1 for root, _, files in os.walk(sample_dir_path, topdown=True)
        for file in files if file.endswith(pattern_to_match1)
    )
    print(f"Generating MEMO matrix from {i} input files.")

    # Generate MEMO matrix
    memo_unaligned = memo.MemoMatrix()
    memo_unaligned.memo_from_unaligned_samples(
        path_to_samples_dir=sample_dir_path,
        pattern_to_match=pattern_to_match1,
        min_relative_intensity=min_relative_intensity,
        max_relative_intensity=max_relative_intensity,
        min_peaks_required=min_peaks_required,
        losses_from=losses_from,
        losses_to=losses_to,
        n_decimals=n_decimals,
    )
    table = memo_unaligned.memo_matrix

    # Filter blanks
    if filter_blanks:
        samples_dir = [directory for directory in os.listdir(sample_dir_path)]
        blanks = []
        for directory in samples_dir:
            metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")
            try:
                metadata = pd.read_csv(metadata_path, sep='\t', usecols=['sample_id', 'sample_type'])
            except IOError:
                continue
            if metadata['sample_type'].eq("blank").any():
                blanks.append(metadata['sample_id'].values[0])
        blanks = list(set(blanks) & set(table.index))
        table_matched = table.loc[blanks]
        table_matched = table_matched.loc[:, (table_matched != 0).any(axis=0)]
        count_null = table_matched.replace(0, np.nan).isnull().sum()

    if word_max_occ_blanks != -1:
        excluded_features = count_null[count_null < (len(table_matched) - word_max_occ_blanks)].index
        table = table.drop(excluded_features, axis=1)
        table = table.drop(blanks, axis=0)
        table = table.astype(float)
        table = table.loc[:, (table != 0).any(axis=0)]

    if ionization in ['pos', 'both']:
        table = table.add_suffix('_pos')
    elif ionization == 'neg':
        table = table.add_suffix('_neg')

    table1 = table.reset_index().rename(columns={'index': 'filename'})

    # Process second pattern for 'both' ionization modes
    if pattern_to_match2:
        i = sum(
            1 for root, _, files in os.walk(sample_dir_path, topdown=True)
            for file in files if file.endswith(pattern_to_match2)
        )
        print(f"Generating MEMO matrix from {i} input files.")
        memo_unaligned.memo_from_unaligned_samples(
            path_to_samples_dir=sample_dir_path,
            pattern_to_match=pattern_to_match2,
            min_relative_intensity=min_relative_intensity,
            max_relative_intensity=max_relative_intensity,
            min_peaks_required=min_peaks_required,
            losses_from=losses_from,
            losses_to=losses_to,
            n_decimals=n_decimals,
        )
        table = memo_unaligned.memo_matrix
        table = table.add_suffix('_neg')
        table2 = table.reset_index().rename(columns={'index': 'filename'})
        table1 = table1.merge(table2, on='filename')

    # Export results
    PATH = os.path.normpath(output_path)
    os.makedirs(PATH, exist_ok=True)

    resolved_output_file = f"{PATH}/{output}.gz"
    resolved_params_file = f"{PATH}/{output}_params.csv"

    datatable = dt.Frame(table1)
    datatable.to_csv(resolved_output_file, compression="gzip")

    # Save parameters
    params = pd.DataFrame(list(params_list.items()), columns=['parameter', 'value'])
    included_samples_df = pd.DataFrame({'parameter': ['included_samples'], 'value': [list(table1.filename)]})
    params = pd.concat([params, included_samples_df], ignore_index=True)
    params.to_csv(resolved_params_file, index=False)

    print(f"Results are saved in: {resolved_output_file}")
    print(f"Parameters are saved in: {resolved_params_file}")
