import pandas as pd
import os
from pathlib import Path
import yaml
import git
import time
import gc
from taxonomical_utils import merger, resolver, upper_taxa_lineage_appender, wikidata_fetcher
import opentree
from opentree import OT

def process_sample(directory, path, force_res, params, url, no_match_path):
    metadata_path = os.path.join(path, directory, directory + "_metadata.tsv")
    try:
        with open(metadata_path, 'r') as f:
            metadata = pd.read_csv(f, sep="\t")
    except (FileNotFoundError, NotADirectoryError):
        return

    # Adding securities
    if metadata["sample_type"][0] == "blank":
        print(f"Sample {directory} is a blank sample, skipping ...")
        return
    if metadata["source_taxon"][0] == "nd":
        print(f"No organism species defined for sample {directory}, skipping ...")
        return
    if not pd.isna(metadata["source_taxon"][0]):
        path_to_results_folders = os.path.join(path, directory, "taxo_output/")
        if (os.path.isdir(path_to_results_folders)) & (force_res is False):
            print(f"sample {directory} already processed")
            return
        if not os.path.isdir(path_to_results_folders):
            os.makedirs(path_to_results_folders)
        print(f"processing sample {directory}")

        # First we copy the metadata file to the output folder
        metadata.to_csv(os.path.join(path_to_results_folders, directory + "_metadata.tsv"), sep="\t", index=False)

        # Define file paths for intermediate and final outputs
        input_file = os.path.join(path_to_results_folders, directory + "_metadata.tsv")
        resolved_file = os.path.join(path_to_results_folders, directory + "_resolved.csv")
        upper_taxa_file = os.path.join(path_to_results_folders, directory + "_upper_taxa.csv")
        wd_file = os.path.join(path_to_results_folders, directory + "_wd.csv")
        final_output_file = os.path.join(path_to_results_folders, directory + "_taxo_metadata.tsv")

        # Resolve taxa
        resolved_df = resolver.resolve_taxa(input_file=input_file, output_file=resolved_file, org_column_header="source_taxon")

        if resolved_df is None or resolved_df.empty:
            print(f"No resolved taxa for sample {directory}")
            with open(no_match_path, "a") as no_match_file:
                no_match_file.write(f"{directory}\n")
            return

        else:
            # Append upper taxonomy lineage
            upper_taxa_df = upper_taxa_lineage_appender.append_upper_taxa_lineage(input_file=resolved_file, output_file=upper_taxa_file)

            # Fetch Wikidata information
            wd_results = []
            for ott_id in resolved_df["taxon.ott_id"]:
                print(f"Fetching data for OTT ID {ott_id}")
                result_df = wikidata_fetcher.wd_taxo_fetcher_from_ott(url, ott_id)
                if not result_df.empty:
                    wd_results.append(result_df)
                else:
                    wd_results.append(pd.DataFrame(columns=["ott.type", "ott.value", "wd.type", "wd.value", "img.type", "img.value"]))

            wd_df = pd.concat(wd_results, ignore_index=True)
            wd_df.to_csv(wd_file, index=False)

            # Merge data
            merged_df = merger.merge_files(input_file=input_file, resolved_taxa_file=resolved_file, upper_taxa_lineage_file=upper_taxa_file, wd_file=wd_file, output_file=final_output_file, org_column_header="source_taxon", delimiter="\t", remove_intermediate=True)

        with open(os.path.join(path_to_results_folders, "params.yaml"), "w") as file:
            yaml.dump(params, file)
        
        # Clean up DataFrames to free memory
        del metadata, resolved_df, upper_taxa_df, wd_df, merged_df
        gc.collect()

if __name__ == "__main__":
    start_time = time.time()
    
    p = Path(__file__).parents[1]
    os.chdir(p)
    url = "https://query.wikidata.org/sparql"

    # Loading the parameters from yaml file
    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    with open(r'../params/user.yml') as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Parameters can now be accessed using params_list_full['level1']['level2']
    sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
    force_res = params_list_full['taxo-info-fetching']['recompute']

    params = {"git": {}, "package_versions": {}, "ott": {}}
    params["git"]["git_commit"] = git.Repo(search_parent_directories=True).head.object.hexsha
    params["git"]["git_commit_link"] = f"https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}"
    params["package_versions"]["opentree"] = opentree.__version__
    params["ott"]["taxonomy_about"] = OT.about()["taxonomy_about"]

    path = os.path.normpath(sample_dir_path)
    samples_dir = [directory for directory in os.listdir(path)]
    no_match_path = os.path.join(params_list_full['data-organization']['source_metadata_path'], "no_match_samples.txt")

    for directory in samples_dir:
        process_sample(directory, path, force_res, params, url, no_match_path)

    print(f"Done processing samples.")
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time} seconds")
