# graph_builder_config.py

import os
from pathlib import Path
import yaml
import rdflib
from rdflib import Namespace


def load_config():
    p = Path(__file__).parents[2]
    os.chdir(p)

    # Check for the existence of the YAML file
    if not os.path.exists("../params/user.yml"):
        print(
            "No ../params/user.yml: copy from ../params/template.yml and modify according to your needs"
        )
        return None

    with open(r"../params/user.yml") as file:
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    # Extract and return the necessary parameters
    return params_list_full

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

    sample_dir_path = os.path.normpath(
        params_list_full["graph-builder"]["sample_dir_path"]
    )
    output_format = params_list_full["graph-builder"]["graph_format"]
    ionization_mode = params_list_full["graph-builder"]["ionization_mode"]

    WD = Namespace(params_list_full["graph-builder"]["wd_namespace"])
    kg_uri = params_list_full["graph-builder"]["kg_uri"]
    ns_kg = rdflib.Namespace(kg_uri)
    prefix = params_list_full["graph-builder"]["prefix"]
    gnps_dashboard_prefix = params_list_full["graph-builder"]["gnps_dashboard_prefix"]
    gnps_tic_pic_prefix = params_list_full["graph-builder"]["gnps_tic_pic_prefix"]
    massive_prefix = params_list_full["graph-builder"]["massive_prefix"]

    source_taxon_header = params_list_full["graph-builder"]["source_taxon_header"]
    source_id_header = params_list_full["graph-builder"]["source_id_header"]
