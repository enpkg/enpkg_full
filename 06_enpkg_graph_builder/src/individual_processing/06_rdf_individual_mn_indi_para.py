import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, XSD, RDFS
import networkx as nx
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import yaml
import git
import traceback
import sys

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

# Change to the appropriate working directory
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

# Load parameters
if not os.path.exists("../params/user.yml"):
    raise FileNotFoundError("No ../params/user.yml: copy from ../params/template.yml and modify according to your needs")

with open("../params/user.yml") as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Substitute placeholders
params_list_full = substitute_variables(params_list_full)

# Extract relevant paths and settings
sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
ionization_mode = params_list_full["general"]["polarity"]
kg_uri = params_list_full["graph-builder"]["kg_uri"]
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full["graph-builder"]["prefix"]

# Ensure the sample directory exists
if not os.path.exists(sample_dir_path):
    raise FileNotFoundError(f"Sample directory path not found: {sample_dir_path}")

# Define RDF graph namespace manager
g = Graph()
nm = g.namespace_manager
nm.bind(prefix, ns_kg)

# Process a single directory
def process_directory(directory):
    g = Graph()
    nm = g.namespace_manager
    nm.bind(prefix, ns_kg)

    graph_path = os.path.join(sample_dir_path, directory, ionization_mode, 'molecular_network', f"{directory}_mn_{ionization_mode}.graphml")
    graph_metadata_path = os.path.join(sample_dir_path, directory, ionization_mode, 'molecular_network', f"{directory}_mn_metadata_{ionization_mode}.tsv")
    metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

    try:
        # Check for metadata and graph files
        if not os.path.exists(graph_path) or not os.path.exists(metadata_path) or not os.path.exists(graph_metadata_path):
            print(f"Skipping {directory}, missing required files.")
            return f"Skipped {directory} due to missing files."

        metadata = pd.read_csv(metadata_path, sep='\t')

        # Skip QC or Blank samples
        if metadata.sample_type[0].lower() in ["qc", "blank"]:
            print(f"Skipping {directory}, QC or Blank sample.")
            return f"Skipped {directory} due to QC or Blank sample."

        graph = nx.read_graphml(graph_path)
        graph_metadata = pd.read_csv(graph_metadata_path, sep='\t')

        for node in graph.edges(data=True):
            s = node[0]
            t = node[1]
            cosine = node[2]['weight']

            mass_diff = abs(
                float(graph_metadata.loc[graph_metadata.feature_id == int(s), 'precursor_mz'].values[0] -
                      graph_metadata.loc[graph_metadata.feature_id == int(t), 'precursor_mz'].values[0])
            )
            component_index = graph_metadata.loc[graph_metadata.feature_id == int(s), 'component_id'].values[0]

            usi_s = f"mzspec:{metadata['massive_id'][0]}:{metadata.sample_id[0]}_features_ms2_{ionization_mode}.mgf:scan:{s}"
            s_feature_id = rdflib.term.URIRef(kg_uri + f"lcms_feature_{usi_s}")
            usi_t = f"mzspec:{metadata['massive_id'][0]}:{metadata.sample_id[0]}_features_ms2_{ionization_mode}.mgf:scan:{t}"
            t_feature_id = rdflib.term.URIRef(kg_uri + f"lcms_feature_{usi_t}")

            ci_node = rdflib.term.URIRef(kg_uri + f"{metadata.sample_id[0]}_fbmn_{ionization_mode}_componentindex_{component_index}")
            g.add((s_feature_id, ns_kg.has_fbmn_ci, ci_node))
            g.add((t_feature_id, ns_kg.has_fbmn_ci, ci_node))

            link_node = rdflib.term.URIRef(kg_uri + f"lcms_feature_pair_{usi_s}_{usi_t}")
            g.add((link_node, RDF.type, ns_kg.LFpair))
            g.add((link_node, ns_kg.has_cosine, rdflib.term.Literal(cosine, datatype=XSD.float)))
            g.add((link_node, ns_kg.has_mass_difference, rdflib.term.Literal(mass_diff, datatype=XSD.float)))

            mn_params_path = os.path.join(sample_dir_path, directory, ionization_mode, 'molecular_network', 'config.yaml')
            hash_1 = get_hash(mn_params_path)
            data_1 = get_data(mn_params_path)
            mn_params_hash = rdflib.term.URIRef(kg_uri + f"mn_params_{hash_1}")
            g.add((link_node, ns_kg.has_mn_params, mn_params_hash))
            g.add((mn_params_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
            del hash_1, data_1

            if graph_metadata.loc[graph_metadata.feature_id == int(s), 'precursor_mz'].values[0] > \
               graph_metadata.loc[graph_metadata.feature_id == int(t), 'precursor_mz'].values[0]:
                g.add((link_node, ns_kg.has_member_1, s_feature_id))
                g.add((link_node, ns_kg.has_member_2, t_feature_id))
            else:
                g.add((link_node, ns_kg.has_member_1, t_feature_id))
                g.add((link_node, ns_kg.has_member_2, s_feature_id))

        # Save RDF graph
        rdf_output_dir = os.path.join(sample_dir_path, directory, "rdf")
        os.makedirs(rdf_output_dir, exist_ok=True)
        rdf_output_file = os.path.join(rdf_output_dir, f"individual_mn_{ionization_mode}.{output_format}")
        g.serialize(destination=rdf_output_file, format=output_format, encoding="utf-8")
        print(f"Results saved in: {rdf_output_file}")
        return f"Processed {directory}"

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message

# Main function
def main():
    directories = [d for d in os.listdir(sample_dir_path) if os.path.isdir(os.path.join(sample_dir_path, d))]
    if not directories:
        print(f"No directories found in {sample_dir_path}. Ensure the path is correct and contains directories.")
        return

    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, directories)
        for result in results:
            if result:
                print(result)

if __name__ == "__main__":
    main()
