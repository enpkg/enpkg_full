import os
import pandas as pd
import argparse
import textwrap
import rdflib
import json
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from tqdm import tqdm
from pathlib import Path
import sys
import git
import yaml
from concurrent.futures import ProcessPoolExecutor
import traceback

sys.path.append(os.path.join(Path(__file__).parents[1], "functions"))
from hash_functions import get_hash, get_data

p = Path(__file__).parents[2]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists("../params/user.yml"):
    print(
        "No ../params/user.yml: copy from ../params/template.yml and modify according to your needs"
    )
with open(r"../params/user.yml") as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full["graph-builder"]

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']


sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
ionization_mode = params_list_full["general"]["polarity"]


with open(os.path.normpath("data/adducts_formatter.json")) as json_file:
    adducts_dic = json.load(json_file)


g = Graph()
nm = g.namespace_manager
kg_uri = params_list_full["graph-builder"]["kg_uri"]
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full["graph-builder"]["prefix"]
nm.bind(prefix, ns_kg)


def process_directory(directory):

    g = Graph()
    nm = g.namespace_manager
    nm.bind(prefix, ns_kg)

    isdb_path = os.path.join(
        path,
        directory,
        ionization_mode,
        "isdb",
        directory + "_isdb_reweighted_flat_" + ionization_mode + ".tsv",
    )
    metadata_path = os.path.join(path, directory, directory + "_metadata.tsv")
    metadata = pd.read_csv(metadata_path, sep="\t")

    if metadata.sample_type[0] == "qc" or metadata.sample_type[0] == "blank":
        print(f"Skipping {directory}, QC or Blank sample.")
        return f"Skipped {directory} due to QC or Blank sample."

    elif metadata.sample_type[0] == "sample":

        try:
            isdb_annotations = pd.read_csv(isdb_path, sep="\t")
            isdb_annotations.adduct.fillna("[M+H]+", inplace=True)
            isdb_annotations.replace({"adduct": adducts_dic}, inplace=True)

            feature_count = []
            for _, row in isdb_annotations.iterrows():
                feature_count.append(row["feature_id"])
                count = feature_count.count(row["feature_id"])
                InChIkey2D = rdflib.term.URIRef(kg_uri + row["short_inchikey"])

                usi = (
                    "mzspec:"
                    + metadata["massive_id"][0]
                    + ":"
                    + metadata.sample_id[0]
                    + "_features_ms2_"
                    + ionization_mode
                    + ".mgf:scan:"
                    + str(row["feature_id"])
                )
                feature_id = rdflib.term.URIRef(kg_uri + "lcms_feature_" + usi)
                isdb_annotation_id = rdflib.term.URIRef(kg_uri + "isdb_" + usi)

                g.add((feature_id, ns_kg.has_isdb_annotation, isdb_annotation_id))

                isdb_params_path = os.path.join(
                    path, directory, ionization_mode, "isdb", "config.yaml"
                )
                hash_1 = get_hash(isdb_params_path)
                data_1 = get_data(isdb_params_path)
                has_isdb_annotation_hash = rdflib.term.URIRef(
                    kg_uri + "has_isdb_annotation_" + hash_1
                )
                g.add((feature_id, has_isdb_annotation_hash, isdb_annotation_id))
                g.add(
                    (
                        has_isdb_annotation_hash,
                        RDFS.subPropertyOf,
                        rdflib.term.URIRef(kg_uri + "has_isdb_annotation"),
                    )
                )
                g.add(
                    (
                        has_isdb_annotation_hash,
                        ns_kg.has_content,
                        rdflib.term.Literal(data_1),
                    )
                )
                del (hash_1, data_1)

                g.add(
                    (
                        isdb_annotation_id,
                        RDFS.label,
                        rdflib.term.Literal(f"isdb annotation of {usi}"),
                    )
                )
                g.add((isdb_annotation_id, ns_kg.has_InChIkey2D, InChIkey2D))
                g.add(
                    (
                        isdb_annotation_id,
                        ns_kg.has_spectral_score,
                        rdflib.term.Literal(row["score_input"], datatype=XSD.float),
                    )
                )
                g.add(
                    (
                        isdb_annotation_id,
                        ns_kg.has_taxo_score,
                        rdflib.term.Literal(row["score_taxo"], datatype=XSD.float),
                    )
                )
                g.add(
                    (
                        isdb_annotation_id,
                        ns_kg.has_consistency_score,
                        rdflib.term.Literal(
                            row["score_max_consistency"], datatype=XSD.float
                        ),
                    )
                )
                g.add(
                    (
                        isdb_annotation_id,
                        ns_kg.has_final_score,
                        rdflib.term.Literal(row["final_score"], datatype=XSD.float),
                    )
                )
                g.add(
                    (
                        isdb_annotation_id,
                        ns_kg.has_adduct,
                        rdflib.term.Literal(row["adduct"]),
                    )
                )
                g.add((InChIkey2D, RDF.type, ns_kg.InChIkey2D))
                g.add((isdb_annotation_id, RDF.type, ns_kg.IsdbAnnotation))

            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(
                os.path.join(pathout, f"isdb_{ionization_mode}.{output_format}")
            )
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")

            # Save parameters:
            params_path = os.path.join(
                sample_dir_path, directory, "rdf", "graph_params.yaml"
            )

            if os.path.isfile(params_path):
                with open(params_path, encoding="UTF-8") as file:
                    params_list = yaml.load(file, Loader=yaml.FullLoader)
            else:
                params_list = {}

            # params_list.update({f'isdb_{ionization_mode}':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
            #                     {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})

            # Retrieve the current Git commit hash
            git_commit_hash = git.Repo(
                search_parent_directories=True
            ).head.object.hexsha

            # Update params_list with version information in a dictionary format
            params_list[f"isdb_{ionization_mode}"] = {
                "git_commit": git_commit_hash,
                "git_commit_link": f"https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}",
            }

            with open(os.path.join(params_path), "w", encoding="UTF-8") as file:
                yaml.dump(params_list, file)

            print(f"Results are in : {pathout}")

        except Exception as e:
            error_message = (
                f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
            )
            print(error_message)
            return error_message


# The main portion of your script would then use a ProcessPoolExecutor
# to process multiple directories in parallel.

# Assuming 'path' is the directory where all your sample directories are located

path = os.path.normpath(sample_dir_path)
samples_dir = [
    directory for directory in os.listdir(path) if not directory.startswith(".")
]
df_list = []


def main():
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, samples_dir)
        for result in results:
            if isinstance(result, str) and "Error processing" in result:
                print("Stopping script due to an error in a worker process.")
                executor.shutdown(wait=False)  # Stop all running workers
                sys.exit(1)  # Exit the main script


# Ensure running main function when the script is executed
if __name__ == "__main__":
    main()
