import os
import pandas as pd
import json
import rdflib
from rdflib import Graph, RDF, RDFS, XSD
from pathlib import Path
import yaml
import git
from concurrent.futures import ProcessPoolExecutor
import traceback


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

    # Context for substitution
    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"]
    }
    recurse_dict(config, context)
    return config


# Set up paths and load YAML configuration
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    raise FileNotFoundError('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute variables in YAML
params_list_full = substitute_variables(params_list_full)

# Extract relevant parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
ionization_mode = params_list_full['general']['polarity']
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

# Ensure the substituted `sample_dir_path` exists
if not os.path.exists(sample_dir_path):
    raise FileNotFoundError(f"Sample directory path not found: {sample_dir_path}")

with open(os.path.normpath('data/adducts_formatter.json')) as json_file:
    adducts_dic = json.load(json_file)


def process_directory(directory):
    """Process a single directory."""
    try:
        isdb_path = os.path.join(sample_dir_path, directory, ionization_mode, 'isdb', f"{directory}_isdb_reweighted_flat_{ionization_mode}.tsv")
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

        if not os.path.exists(isdb_path) or not os.path.exists(metadata_path):
            print(f"Skipping {directory}, missing ISDB or metadata file.")
            return

        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] in ['QC', 'Blank']:
            print(f"Skipping {directory}, QC or Blank sample.")
            return

        # Process valid sample directories
        isdb_annotations = pd.read_csv(isdb_path, sep='\t')
        isdb_annotations.adduct.fillna('[M+H]+', inplace=True)
        isdb_annotations.replace({"adduct": adducts_dic}, inplace=True)

        g = Graph()
        g.namespace_manager.bind(prefix, ns_kg)

        for _, row in isdb_annotations.iterrows():
            feature_id = row['feature_id']
            usi = f"mzspec:{metadata['massive_id'][0]}:{metadata.sample_id[0]}_features_ms2_{ionization_mode}.mgf:scan:{feature_id}"
            feature_uri = rdflib.URIRef(kg_uri + f"lcms_feature_{usi}")
            isdb_annotation_uri = rdflib.URIRef(kg_uri + f"isdb_{usi}")
            InChIkey2D = rdflib.URIRef(kg_uri + row['short_inchikey'])

            # Link feature to ISDB annotation
            g.add((feature_uri, ns_kg.has_isdb_annotation, isdb_annotation_uri))
            g.add((isdb_annotation_uri, RDFS.label, rdflib.Literal(f"ISDB annotation of {usi}")))
            g.add((isdb_annotation_uri, ns_kg.has_InChIkey2D, InChIkey2D))
            g.add((isdb_annotation_uri, ns_kg.has_spectral_score, rdflib.Literal(row['score_input'], datatype=XSD.float)))
            g.add((isdb_annotation_uri, ns_kg.has_taxo_score, rdflib.Literal(row['score_taxo'], datatype=XSD.float)))
            g.add((isdb_annotation_uri, ns_kg.has_consistency_score, rdflib.Literal(row['score_max_consistency'], datatype=XSD.float)))
            g.add((isdb_annotation_uri, ns_kg.has_final_score, rdflib.Literal(row['final_score'], datatype=XSD.float)))
            g.add((isdb_annotation_uri, ns_kg.has_adduct, rdflib.Literal(row['adduct'])))
            g.add((InChIkey2D, RDF.type, ns_kg.InChIkey2D))
            g.add((isdb_annotation_uri, RDF.type, ns_kg.IsdbAnnotation))

        # Save RDF graph
        rdf_output_dir = os.path.join(sample_dir_path, directory, "rdf")
        os.makedirs(rdf_output_dir, exist_ok=True)
        rdf_output_file = os.path.join(rdf_output_dir, f"isdb_{ionization_mode}.{output_format}")
        g.serialize(destination=rdf_output_file, format=output_format, encoding="utf-8")
        print(f"Results saved in: {rdf_output_file}")

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)


def main():
    directories = [d for d in os.listdir(sample_dir_path) if os.path.isdir(os.path.join(sample_dir_path, d))]

    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, directories)
        for result in results:
            if result:
                print(result)


if __name__ == "__main__":
    main()
