import memo_ms as memo
import os
import datatable as dt
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import shutil


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
        "general.root_data_path": config.get("general", {}).get("root_data_path", ""),
        "general.treated_data_path": config.get("general", {}).get("treated_data_path", ""),
        "general.polarity": config.get("general", {}).get("polarity", ""),
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

    # Local temporary save path
    local_output_path = "/tmp/memo_matrix"
    os.makedirs(local_output_path, exist_ok=True)

    # Debug: Verify resolved paths
    print(f"Resolved output path: {output_path}")
    print(f"Resolved local temporary path: {local_output_path}")

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

    # Export results locally
    local_resolved_output_file = f"{local_output_path}/{output}.gz"
    local_resolved_params_file = f"{local_output_path}/{output}_params.csv"

    datatable = dt.Frame(table.reset_index().rename(columns={'index': 'filename'}))
    datatable.to_csv(local_resolved_output_file, compression="gzip")

    # Save parameters locally
    params = pd.DataFrame(list(params_list.items()), columns=['parameter', 'value'])
    included_samples_df = pd.DataFrame({'parameter': ['included_samples'], 'value': [list(table.index)]})
    params = pd.concat([params, included_samples_df], ignore_index=True)
    params.to_csv(local_resolved_params_file, index=False)

    # Attempt to copy results to the network drive
    try:
        resolved_output_file = f"{output_path}/{output}.gz"
        resolved_params_file = f"{output_path}/{output}_params.csv"

        os.makedirs(output_path, exist_ok=True)
        shutil.copy(local_resolved_output_file, resolved_output_file)
        shutil.copy(local_resolved_params_file, resolved_params_file)

        print(f"Results successfully copied to: {resolved_output_file}")
        print(f"Parameters successfully copied to: {resolved_params_file}")
    except Exception as e:
        print(f"Error copying files to network drive: {e}")
        print(f"Results remain saved locally at: {local_resolved_output_file}")
        print(f"Parameters remain saved locally at: {local_resolved_params_file}")
