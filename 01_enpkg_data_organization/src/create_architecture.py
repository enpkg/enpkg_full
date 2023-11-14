"""Argument parser """
import argparse
import os
import shutil
import textwrap
import pandas as pd
import yaml

from userinput.utils import must_be_in_set
from pathlib import Path



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
        The path to the directory where data files are located
    target_path : str
        The path to the directory where files will be moved
    source_metadata_path : str
        The path to the directory where metadata files are located
    metadata_filename : str
        The name of the metadata file to use (it has to be located in sample_dir_path)
    lcms_method_filename : str
        The name of the metadata file to use (it has to be located in sample_dir_path)
    lcms_processing_filename : str
        The name of the metadata file to use (it has to be located in sample_dir_path)
    polarity : str
        The polarity mode of LC-MS/MS analyses
        It has to be one of ["pos", "neg"].

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
    # Create target path if does not exist
    if not os.path.isdir(target_path):
        os.makedirs(target_path)

    # List folder content
    df_metadata = pd.read_csv(path_metadata, sep="\t")
    if not os.path.isdir(os.path.join(target_path, f"for_massive_upload_{polarity}")):
        os.makedirs(os.path.join(target_path, f"for_massive_upload_{polarity}"))
    for i, row in df_metadata.iterrows():
        sample_id = row["sample_id"]
        if polarity == "pos":
            sample_filename = row["sample_filename_pos"]
            sample_filename_woext = sample_filename.rsplit(".", 1)[0]
        elif polarity == "neg":
            sample_filename = row["sample_filename_neg"]
            sample_filename_woext = sample_filename.rsplit(".", 1)[0]

        # create sample's folder if if it does not exist yet
        sample_folder = os.path.join(target_path, sample_id)
        if not os.path.isdir(sample_folder):
            os.makedirs(sample_folder)

        # create individual metadata file
        pd.DataFrame(
            df_metadata.iloc[i],
        ).transpose().to_csv(
            os.path.join(target_path, sample_id, sample_id + "_metadata.tsv"),
            sep="\t",
            index=False,
        )

        # move and rename sample's files
        sub_folder = os.path.normpath(os.path.join(sample_folder, polarity + "/"))
        if not os.path.isdir(sub_folder):
            os.makedirs(sub_folder)

        for file in os.listdir(source_path):
            if file.startswith(sample_filename_woext):
                shutil.copy(os.path.join(source_path, file), sub_folder)

        if len(os.listdir(sub_folder)) == 0:
            print(f"No matched file for sample {sample_id}")
        elif len(os.listdir(sub_folder)) == 1:
            print(f"1 matched file for sample {sample_id}")
        elif len(os.listdir(sub_folder)) == 2:
            print(f"2 matched file for sample {sample_id}")
        elif len(os.listdir(sub_folder)) == 3:
            print(f"3 matched file for sample {sample_id}")

        for file in os.listdir(sub_folder):
            file_path = os.path.normpath(os.path.join(sub_folder + "/" + file))


            lcms_method_extension = path_lcms_method_filename.split(".", 1)[1]
            lcms_processing_extension = path_lcms_processing_filename.split(".", 1)[1]
            destination_path_lcms_method_filename = os.path.join(
                sub_folder,
                f"{sample_id}_lcms_method_params_{polarity}.{lcms_method_extension}",
            )
            destination_path_lcms_processing_filename = os.path.join(
                sub_folder,
                f"{sample_id}_lcms_processing_params_{polarity}.{lcms_processing_extension}",
            )
            os.makedirs(os.path.dirname(destination_path_lcms_method_filename), exist_ok=True)
            os.makedirs(os.path.dirname(destination_path_lcms_processing_filename), exist_ok=True)
            os.makedirs(sub_folder, exist_ok=True)
            shutil.copyfile(
                path_lcms_method_filename, destination_path_lcms_method_filename
            )
            shutil.copyfile(
                path_lcms_processing_filename, destination_path_lcms_processing_filename
            )

            if file.endswith(".csv"):
                os.rename(
                    file_path,
                    os.path.join(
                        sub_folder, f"{sample_id}_features_quant_{polarity}.csv"
                    ),
                )
            elif file.endswith("_sirius.mgf"):
                os.rename(
                    file_path,
                    os.path.join(sub_folder, f"{sample_id}_sirius_{polarity}.mgf"),
                )
            elif file.endswith(".mgf"):
                os.rename(
                    file_path,
                    os.path.join(
                        sub_folder, f"{sample_id}_features_ms2_{polarity}.mgf"
                    ),
                )
                shutil.copy(
                    (sub_folder + "/" + f"{sample_id}_features_ms2_{polarity}.mgf"),
                    os.path.join(target_path, f"for_massive_upload_{polarity}"),
                )


if __name__ == "__main__":
    os.chdir(os.getcwd())

    p = Path(__file__).parents[1]
    os.chdir(p)

    # Loading the parameters from yaml file

    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    with open (r'../params/user.yml') as file:    
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    params_list = params_list_full['data-organization']

    # Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

    organize_folder(
        source_path=os.path.normpath(params_list['source_path']),
        target_path=os.path.normpath(params_list['target_path']),
        source_metadata_path=params_list['source_metadata_path'],
        metadata_filename=params_list['sample_metadata_filename'],
        lcms_method_filename=params_list['lcms_method_params_filename'],
        lcms_processing_filename=params_list['lcms_processing_params_filename'],
        polarity=params_list['polarity']
    )
