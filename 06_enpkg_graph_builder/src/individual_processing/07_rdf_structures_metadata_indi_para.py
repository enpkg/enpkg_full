import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS
import sqlite3
import argparse
import textwrap
from pathlib import Path
from tqdm import tqdm
import git
import yaml
from concurrent.futures import ProcessPoolExecutor
import traceback

# These lines allows to make sure that we are placed at the repo directory level 
p = Path(__file__).parents[2]
os.chdir(p)

# Function to substitute variables in YAML
def substitute_variables(config):
    """Recursively substitute placeholders in the YAML configuration."""
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

    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config

# Load parameters from YAML
if not os.path.exists("../params/user.yml"):
    raise FileNotFoundError("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")

with open("../params/user.yml") as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute placeholders
params_list_full = substitute_variables(params_list_full)

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
ionization_mode = params_list_full['general']['polarity']

metadata_path = params_list_full['graph-builder']['structures_db_path']

greek_alphabet = 'ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩωÎ²Iµ'
latin_alphabet = 'AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtUuFfQqYyWwI2Iu'
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)

# Connect to structures DB
print(f'Connecting to structures DB: {metadata_path}')
dat = sqlite3.connect(metadata_path)
query = dat.execute("SELECT * From structures_metadata")
cols = [column[0] for column in query.description]
df_metadata = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)

kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path) if not directory.startswith('.')]

def process_directory(args):
    try:
        # Unpack arguments
        directory, path, df_metadata = args

        metadata_path = os.path.join(path, directory, f"{directory}_metadata.tsv")
        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] == 'qc' or metadata.sample_type[0] == 'blank':
            print(f'Skipping {directory}, QC or Blank sample.')
            return f'Skipped {directory} due to QC or Blank sample.'

        elif metadata.sample_type[0] == 'sample':
            paths = []
            isdb_pos_path = os.path.join(path, directory, f'rdf/isdb_pos.{output_format}')
            isdb_neg_path = os.path.join(path, directory, f'rdf/isdb_neg.{output_format}')
            sirius_pos_path = os.path.join(path, directory, f'rdf/sirius_pos.{output_format}')
            sirius_neg_path = os.path.join(path, directory, f'rdf/sirius_neg.{output_format}')

            paths = [isdb_pos_path, isdb_neg_path, sirius_pos_path, sirius_neg_path]
            path_exist = []
            for path_annot in paths:
                if os.path.isfile(path_annot):
                    path_exist.append(path_annot)
                else:
                    pass

            merged_graph = Graph()
            nm = merged_graph.namespace_manager
            nm.bind(prefix, ns_kg)
            for path_annot in path_exist:
                with open(path_annot, "r") as f:
                    file_content = f.read()
                    merged_graph.parse(data=file_content, format=output_format)

            sample_short_ik = []
            for s, p, o in merged_graph.triples((None, RDF.type, ns_kg.InChIkey2D)):
                sample_short_ik.append(s[-14:])

            sample_specific_db = df_metadata[df_metadata['short_inchikey'].isin(sample_short_ik)]

            g = Graph()
            nm = g.namespace_manager
            nm.bind(prefix, ns_kg)

            # Process each row in sample_specific_db
            for _, row in sample_specific_db.iterrows():
                short_ik = rdflib.term.URIRef(kg_uri + row['short_inchikey'])
                npc_pathway_list = row['npc_pathway'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')
                npc_superclass_list = row['npc_superclass'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')
                npc_class_list = row['npc_class'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')

                npc_pathway_urilist = []
                npc_superclass_urilist = []
                npc_class_urilist = []

                for lst, uri_list in zip([npc_pathway_list, npc_superclass_list, npc_class_list],
                                         [npc_pathway_urilist, npc_superclass_urilist, npc_class_urilist]):
                    for item in lst:
                        uri_list.append(rdflib.term.URIRef(kg_uri + "npc_" + item))

                g.add((short_ik, ns_kg.has_smiles, rdflib.term.Literal(row['smiles'])))

                for uri in npc_pathway_urilist:
                    g.add((short_ik, ns_kg.has_npc_pathway, uri))
                    g.add((uri, RDF.type, ns_kg.NPCPathway))
                for uri in npc_superclass_urilist:
                    g.add((short_ik, ns_kg.has_npc_superclass, uri))
                    g.add((uri, RDF.type, ns_kg.NPCSuperclass))
                for uri in npc_class_urilist:
                    g.add((short_ik, ns_kg.has_npc_class, uri))
                    g.add((uri, RDF.type, ns_kg.NPCClass))

                if (row['wikidata_id'] != 'no_wikidata_match') and (row['wikidata_id'] is not None):
                    g.add((short_ik, ns_kg.is_InChIkey2D_of, rdflib.term.URIRef(kg_uri + row['inchikey'])))
                    g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_wd_id, rdflib.term.URIRef(row['wikidata_id'])))
                    g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), RDF.type, ns_kg.InChIkey))

            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(os.path.join(pathout, f'structures_metadata.{output_format}'))
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")

            print(f"Results are in: {pathout}")

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message


def main():
    args = [(directory, path, df_metadata) for directory in samples_dir]
    with ProcessPoolExecutor(max_workers=32) as executor:
        for result in executor.map(process_directory, args):
            if isinstance(result, str) and "Error processing" in result:
                print(result)


if __name__ == "__main__":
    main()
