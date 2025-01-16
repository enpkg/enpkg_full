import argparse
import os
import shutil
import textwrap
import pandas as pd
import yaml

from userinput.utils import must_be_in_set
from pathlib import Path


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


def organize_folder(
    source_path: str,
    target_path: str,
    source_metadata_path: str,
    metadata_filename: str,
    lcms_method_filename: str,
    lcms_processing_filename: str,
    polarity: str,
):
    """Organize folder with unaligned feature list files and their aggregated metadata in individual folders.

    Parameters
    ----------
    source_path : str
        The path to the directory where data files are located.
    target_path : str
        The path to the directory where files will be moved.
    source_metadata_path : str
        The path to the directory where metadata files are located.
    metadata_filename : str
        The name of the metadata file to use (it has to be located in source_metadata_path).
    lcms_method_filename : str
        The name of the LC-MS method parameters file to use (located in source_metadata_path).
    lcms_processing_filename : str
        The name of the LC-MS processing parameters file to use (located in source_metadata_path).
    polarity : str
        The polarity mode of LC-MS/MS analyses; must be one of ["pos", "neg"].

    Raises
    ------
    ValueError
        If polarity is not one of ["pos", "neg"].
    """
    polarity = must_be_in_set(polarity, ["pos", "neg"], "polarity")
    path_metadata = os.path.join(source_metadata_path, metadata_filename)
    path_lcms_method_filename = os.path.join(source_metadata_path, lcms_method_filename)
    path_lcms_processing_filename = os.path.join(
        source_metadata_path, lcms_processing_filename
    )

    # Create target path if it doesn't exist
    if not os.path.isdir(target_path):
        os.makedirs(target_path)

    # Read metadata file
    df_metadata = pd.read_csv(path_metadata, sep="\t")

    # Create directory for massive upload if it doesn't exist
    massive_upload_dir = os.path.join(target_path, f"../for_massive_upload_{polarity}")
    if not os.path.isdir(massive_upload_dir):
        os.makedirs(massive_upload_dir)

    # Process each sample
    for i, row in df_metadata.iterrows():
        sample_id = row["sample_id"]

        # Check if the sample_filename column for the current polarity is valid
        sample_filename = row.get(f"sample_filename_{polarity}")
        if pd.isna(sample_filename) or not isinstance(sample_filename, str):
            print(f"Skipping sample {sample_id}: Invalid or missing filename for polarity '{polarity}'.")
            continue

        try:
            # Remove the file extension
            sample_filename_woext = sample_filename.rsplit(".", 1)[0]
        except Exception as e:
            print(f"Error processing sample {sample_id}: {e}")
            continue

        # Create sample's folder
        sample_folder = os.path.join(target_path, sample_id)
        if not os.path.isdir(sample_folder):
            os.makedirs(sample_folder)

        # Create individual metadata file
        pd.DataFrame(df_metadata.iloc[i]).transpose().to_csv(
            os.path.join(sample_folder, f"{sample_id}_metadata.tsv"), sep="\t", index=False
        )

        # Create polarity-specific subfolder
        sub_folder = os.path.normpath(os.path.join(sample_folder, polarity + "/"))
        if not os.path.isdir(sub_folder):
            os.makedirs(sub_folder)

        # Copy and rename sample files
        for file in os.listdir(source_path):
            if file.startswith(sample_filename_woext):
                shutil.copy(os.path.join(source_path, file), sub_folder)

        # Handle LC-MS method and processing files
        lcms_method_extension = lcms_method_filename.split(".", 1)[1]
        lcms_processing_extension = lcms_processing_filename.split(".", 1)[1]

        destination_path_lcms_method_filename = os.path.join(
            sub_folder, f"{sample_id}_lcms_method_params_{polarity}.{lcms_method_extension}"
        )
        destination_path_lcms_processing_filename = os.path.join(
            sub_folder, f"{sample_id}_lcms_processing_params_{polarity}.{lcms_processing_extension}"
        )
        shutil.copyfile(path_lcms_method_filename, destination_path_lcms_method_filename)
        shutil.copyfile(
            path_lcms_processing_filename, destination_path_lcms_processing_filename
        )

        # Rename files based on type
        for file in os.listdir(sub_folder):
            file_path = os.path.normpath(os.path.join(sub_folder, file))
            if file.endswith(".csv"):
                os.rename(
                    file_path,
                    os.path.join(sub_folder, f"{sample_id}_features_quant_{polarity}.csv"),
                )
            elif file.endswith("_sirius.mgf"):
                os.rename(
                    file_path,
                    os.path.join(sub_folder, f"{sample_id}_sirius_{polarity}.mgf"),
                )
            elif file.endswith(".mgf"):
                os.rename(
                    file_path,
                    os.path.join(sub_folder, f"{sample_id}_features_ms2_{polarity}.mgf"),
                )
                shutil.copy(
                    os.path.join(sub_folder, f"{sample_id}_features_ms2_{polarity}.mgf"),
                    massive_upload_dir,
                )


if __name__ == "__main__":
    os.chdir(os.getcwd())

    p = Path(__file__).parents[1]
    os.chdir(p)

    # Load YAML configuration
    if not os.path.exists("../params/user.yml"):
        print("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")
        exit()

    with open(r"../params/user.yml") as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Apply variable substitution
    params_list_full = substitute_variables(params_list_full)

    # Extract parameters
    source_path = os.path.normpath(params_list_full["data-organization"]["source_path"])
    target_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
    source_metadata_path = os.path.normpath(params_list_full["data-organization"]["source_metadata_path"])
    metadata_filename = params_list_full["data-organization"]["sample_metadata_filename"]
    lcms_method_filename = params_list_full["data-organization"]["lcms_method_params_filename"]
    lcms_processing_filename = params_list_full["data-organization"]["lcms_processing_params_filename"]
    polarity = params_list_full["general"]["polarity"]

    # Debug: Print paths to confirm substitution
    print(f"Source Path: {source_path}")
    print(f"Target Path: {target_path}")
    print(f"Metadata File Path: {os.path.join(source_metadata_path, metadata_filename)}")

    # Check if metadata file exists
    metadata_file_path = os.path.join(source_metadata_path, metadata_filename)
    if not os.path.exists(metadata_file_path):
        print(f"Metadata file not found: {metadata_file_path}")
        exit()

    # Organize folder
    organize_folder(
        source_path=source_path,
        target_path=target_path,
        source_metadata_path=source_metadata_path,
        metadata_filename=metadata_filename,
        lcms_method_filename=lcms_method_filename,
        lcms_processing_filename=lcms_processing_filename,
        polarity=polarity,
    )
