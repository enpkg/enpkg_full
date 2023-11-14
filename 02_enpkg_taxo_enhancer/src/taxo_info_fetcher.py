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



def wd_taxo_fetcher_from_ott(url: str, ott_id: int):
    query = f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?ott ?wd ?img
    WHERE{{
        ?wd wdt:P9157 ?ott
        OPTIONAL{{ ?wd wdt:P18 ?img }}
        VALUES ?ott {{'{ott_id}'}}
    }}
    """

    r = requests.get(url, params={"format": "json", "query": query}, timeout=10)

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


if __name__ == "__main__":
    p = Path(__file__).parents[1]
    os.chdir(p)
    url = "https://query.wikidata.org/sparql"

    # Loading the parameters from yaml file

    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    with open (r'../params/user.yml') as file:    
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    params_list = params_list_full['taxo-info-fetching']

    # Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

    sample_dir_path = os.path.normpath(params_list['sample_dir_path'])
    force_res = params_list['recompute']

    params = {"git": [], "package_versions": [], "ott": []}

    params["git"].append(
        {"git_commit": git.Repo(search_parent_directories=True).head.object.hexsha}
    )
    params["git"].append(
        {
            "git_commit_link": f"https://github.com/enpkg/enpkg_taxo_enhancer/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}"
        }
    )

    params["package_versions"].append({"opentree": opentree.__version__})

    params["ott"].append(OT.about()["taxonomy_about"])

    path = os.path.normpath(sample_dir_path)
    samples_dir = [directory for directory in os.listdir(path)]
    df_list = []

    no_match = []
    for directory in samples_dir:
        metadata_path = os.path.join(path, directory, directory + "_metadata.tsv")
        try:
            metadata = pd.read_csv(metadata_path, sep="\t")
        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue

        # Adding securities
        if metadata["sample_type"][0] == "blank":
            print(f"Sample {directory} is a blank sample, skipping ...")
            continue
        if metadata["source_taxon"][0] == "nd":
            print(f"No organism species defined for sample {directory}, skipping ...")
            continue
        if pd.isna(metadata["source_taxon"][0]) is False:
            path_to_results_folders = os.path.join(path, directory, "taxo_output/")
            if (os.path.isdir(path_to_results_folders)) & (force_res is False):
                print(f"sample {directory} already processed")
                continue
            if not os.path.isdir(path_to_results_folders):
                os.makedirs(path_to_results_folders)
            print(f"processing sample {directory}")
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

        else:
            continue

    print(f"Done, no match for samples: {no_match}")
