import pandas as pd
import numpy as np
from pandas import json_normalize
import requests
import os
from taxo_resolver import *
from pathlib import Path
import argparse
import textwrap
import yaml
import git
import opentree
from opentree import OT
import time


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


def wd_taxo_fetcher_from_ott(url: str, ott_id: int):
    """Fetch taxonomical data from Wikidata for a given OTT ID."""
    query = f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?ott ?wd ?img
    WHERE{{
        ?wd wdt:P9157 ?ott
        OPTIONAL{{ ?wd wdt:P18 ?img }}
        VALUES ?ott {{'{ott_id}'}}
    }}
    """
    try:
        r = requests.get(url, params={"format": "json", "query": query}, timeout=10)
        if r.status_code != 200 or not r.content:
            return pd.DataFrame(
                data={
                    "ott.type": [np.NaN],
                    "ott.value": [np.NaN],
                    "wd.type": [np.NaN],
                    "wd.value": [np.NaN],
                }
            )
        data = r.json()
        results = pd.DataFrame.from_dict(data).results.bindings
        df = json_normalize(results)
        if len(df) == 0:
            df = pd.DataFrame(
                data={
                    "ott.type": [np.NaN],
                    "ott.value": [np.NaN],
                    "wd.type": [np.NaN],
                    "wd.value": [np.NaN],
                }
            )
        return df

    except requests.exceptions.RequestException as e:
        print(f"Request failed for ott_id: {ott_id} with exception: {e}")
        return pd.DataFrame(
            data={
                "ott.type": [np.NaN],
                "ott.value": [np.NaN],
                "wd.type": [np.NaN],
                "wd.value": [np.NaN],
            }
        )


if __name__ == "__main__":
    # Ensure script operates in its parent directory
    p = Path(__file__).parents[1]
    os.chdir(p)

    # Define the SPARQL endpoint URL
    url = "https://query.wikidata.org/sparql"

    # Load parameters from YAML file
    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
        exit()

    with open(r'../params/user.yml') as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Perform variable substitution in YAML
    params_list_full = substitute_variables(params_list_full)

    # Extract parameters from YAML
    sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
    force_res = params_list_full['taxo-info-fetching']['recompute']

    # Initialize metadata for logging and debugging
    params = {"git": {}, "package_versions": {}, "ott": {}}
    repo = git.Repo(search_parent_directories=True)
    params["git"]["git_commit"] = repo.head.object.hexsha
    params["git"]["git_commit_link"] = f"https://github.com/enpkg/enpkg_full/tree/{repo.head.object.hexsha}"
    params["package_versions"]["opentree"] = opentree.__version__
    params["ott"]["taxonomy_about"] = OT.about()["taxonomy_about"]

    # Prepare to process samples
    path = os.path.normpath(sample_dir_path)
    samples_dir = [directory for directory in os.listdir(path)]
    df_list = []

    no_match = []
    for directory in samples_dir:
        metadata_path = os.path.join(path, directory, directory + "_metadata.tsv")
        try:
            metadata = pd.read_csv(metadata_path, sep="\t")
        except FileNotFoundError:
            print(f"Metadata file not found for sample {directory}, skipping...")
            continue
        except NotADirectoryError:
            print(f"Invalid directory structure for sample {directory}, skipping...")
            continue

        # Skip blank samples or samples with no defined organism species
        if metadata["sample_type"][0] == "blank":
            print(f"Sample {directory} is a blank sample, skipping...")
            continue
        if metadata["source_taxon"][0] == "nd":
            print(f"No organism species defined for sample {directory}, skipping...")
            continue

        if pd.notna(metadata["source_taxon"][0]):
            path_to_results_folders = os.path.join(path, directory, "taxo_output/")
            if os.path.isdir(path_to_results_folders) and not force_res:
                print(f"Sample {directory} already processed, skipping...")
                continue

            os.makedirs(path_to_results_folders, exist_ok=True)
            print(f"Processing sample {directory}...")

            taxo_df = taxa_lineage_appender(
                metadata, "source_taxon", True, path_to_results_folders, directory
            )
            if taxo_df["matched_name"][0] == "None":
                print(f"No matched species for sample {directory}")
                no_match.append(directory)
                continue

            wd_df = wd_taxo_fetcher_from_ott(url, taxo_df["ott_id"][0])
            path_taxo_df = os.path.join(
                path_to_results_folders, directory + "_taxo_metadata.tsv"
            )
            taxo_df.join(wd_df).to_csv(path_taxo_df, sep="\t")

            with open(
                os.path.join(path_to_results_folders, "params.yaml"), "w"
            ) as file:
                yaml.dump(params, file)

    print(f"Done. No match for samples: {no_match}")
