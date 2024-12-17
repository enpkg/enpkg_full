import os
import json
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import yaml
import git
import traceback

# Function to substitute variables in YAML
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

# Load and substitute variables in the YAML configuration
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    exit()

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
ionization_mode = params_list_full['general']['polarity']
output_format = params_list_full['graph-builder']['graph_format']
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

print(f"Resolved sample_dir_path: {sample_dir_path}")
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    exit()

with open(os.path.normpath('data/adducts_formatter.json')) as json_file:
    adducts_dic = json.load(json_file)

# Processing function for each directory
def process_directory(directory):
    g = Graph()
    g.namespace_manager.bind(prefix, ns_kg)

    csi_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_WORKSPACE_SIRIUS", 'compound_identifications.tsv')
    metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

    try:
        if not os.path.exists(csi_path) or not os.path.exists(metadata_path):
            print(f"Skipping {directory}, missing files.")
            return f"Skipped {directory} due to missing files."

        csi_annotations = pd.read_csv(csi_path, sep='\t')
        metadata = pd.read_csv(metadata_path, sep='\t')
        csi_annotations.replace({"adduct": adducts_dic}, inplace=True)

        for _, row in csi_annotations.iterrows():
            feature_id_int = row['id'].rsplit('_', 1)[1]
            usi = f"mzspec:{metadata['massive_id'][0]}:{metadata['sample_id'][0]}_features_ms2_{ionization_mode}.mgf:scan:{int(feature_id_int)}"
            feature_id = rdflib.term.URIRef(f"{kg_uri}lcms_feature_{usi}")
            sirius_annotation_id = rdflib.term.URIRef(f"{kg_uri}sirius_{usi}")
            InChIkey2D = rdflib.term.URIRef(f"{kg_uri}{row['InChIkey2D']}")

            sirius_params_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_WORKSPACE_SIRIUS", 'params.yml')
            hash_1 = hash(sirius_params_path)
            data_1 = open(sirius_params_path).read() if os.path.exists(sirius_params_path) else "No data"

            has_sirius_annotation_hash = rdflib.term.URIRef(f"{kg_uri}has_sirius_annotation_{hash_1}")
            g.add((feature_id, has_sirius_annotation_hash, sirius_annotation_id))
            g.add((has_sirius_annotation_hash, RDFS.subPropertyOf, rdflib.term.URIRef(f"{kg_uri}has_sirius_annotation")))
            g.add((has_sirius_annotation_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))

            g.add((sirius_annotation_id, ns_kg.has_InChIkey2D, InChIkey2D))
            g.add((sirius_annotation_id, ns_kg.has_ionization, rdflib.term.Literal(ionization_mode)))
            g.add((sirius_annotation_id, RDFS.label, rdflib.term.Literal(f"Sirius annotation of {usi}")))
            g.add((sirius_annotation_id, ns_kg.has_sirius_adduct, rdflib.term.Literal(row['adduct'])))
            g.add((sirius_annotation_id, ns_kg.has_sirius_score, rdflib.term.Literal(row['SiriusScore'], datatype=XSD.float)))
            g.add((sirius_annotation_id, ns_kg.has_zodiac_score, rdflib.term.Literal(row['ZodiacScore'], datatype=XSD.float)))
            g.add((sirius_annotation_id, ns_kg.has_cosmic_score, rdflib.term.Literal(row['ConfidenceScore'], datatype=XSD.float)))
            g.add((InChIkey2D, RDF.type, ns_kg.InChIkey2D))
            g.add((sirius_annotation_id, RDF.type, ns_kg.SiriusStructureAnnotation))

        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.join(pathout, f"sirius_{ionization_mode}.{output_format}")
        g.serialize(destination=pathout, format=output_format, encoding="utf-8")

        print(f"Results are in: {pathout}")
        return f"Processed {directory}"

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message

# Main function
def main():
    samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, samples_dir)
    for result in results:
        print(result)

if __name__ == "__main__":
    main()
