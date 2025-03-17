import os
import argparse
import textwrap
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD, FOAF
from tqdm import tqdm
from pathlib import Path
import sys
import git
import yaml
from concurrent.futures import ProcessPoolExecutor
import traceback

# Add custom function path
sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

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

    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config

# Load parameters from YAML
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    sys.exit(1)

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
ionization_mode = params_list_full['general']['polarity']
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

spectrum_dashboard_prefix = params_list_full['graph-builder']['spectrum_dashboard_prefix']
spectrum_png_prefix = params_list_full['graph-builder']['spectrum_png_prefix']
gnps_fast_search_prefix = params_list_full['graph-builder']['gnps_fast_search_prefix']

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path) if not directory.startswith('.')]

# Processing function for a single directory
def process_directory(directory):
    try:
        quant_path = os.path.join(path, directory, ionization_mode, f"{directory}_features_quant_{ionization_mode}.csv")
        metadata_path = os.path.join(path, directory, f"{directory}_metadata.tsv")

        if not os.path.isfile(quant_path) or not os.path.isfile(metadata_path):
            print(f"Missing files: {quant_path} or {metadata_path}, skipping {directory}")
            return

        quant_table = pd.read_csv(quant_path, sep=',')
        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] == 'sample':
            g = Graph()
            g.namespace_manager.bind(prefix, ns_kg)

            sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])
            area_col = [col for col in quant_table.columns if col.endswith(' Peak area')][0]
            max_area = quant_table[area_col].max()

            feature_list = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + f"_lcms_feature_list_{ionization_mode}")
            #TO ADD#g.add((feature_id, RDF.type, ns_kg.LCMSFeatureList))

            # Handle LC-MS parameters
            lc_ms = None
            lcms_processing_params_path = None

            if ionization_mode == 'pos':
                lc_ms = rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0])
                for file in os.listdir(os.path.join(path, directory, "pos")):
                    if file.startswith(f"{directory}_lcms_processing_params_pos"):
                        lcms_processing_params_path = os.path.join(path, directory, "pos", file)
            elif ionization_mode == 'neg':
                lc_ms = rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0])
                for file in os.listdir(os.path.join(path, directory, "neg")):
                    if file.startswith(f"{directory}_lcms_processing_params_neg"):
                        lcms_processing_params_path = os.path.join(path, directory, "neg", file)

            if lc_ms and lcms_processing_params_path:
                hash_1 = get_hash(lcms_processing_params_path)
                data_1 = get_data(lcms_processing_params_path)
                has_lcms_feature_list_hash = rdflib.term.URIRef(kg_uri + "has_lcms_feature_list_" + hash_1)

                g.add((lc_ms, has_lcms_feature_list_hash, feature_list))
                g.add((has_lcms_feature_list_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_lcms_feature_list')))
                g.add((has_lcms_feature_list_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))

                del hash_1, data_1
                
                g.add((feature_list, RDF.type, ns_kg.LCMSFeatureList))
                g.add((feature_list, ns_kg.has_ionization, rdflib.term.Literal(ionization_mode)))
                g.add((feature_list, RDFS.comment, rdflib.term.Literal(f"LCMS feature list in {ionization_mode} ionization mode of {metadata.sample_id[0]}")))
               
            # Process features and add to graph

            for _, row in quant_table.iterrows():
                usi = (f"mzspec:{metadata['massive_id'][0]}:{metadata.sample_id[0]}"
                       f"_features_ms2_{ionization_mode}.mgf:scan:{int(row['row ID'])}")
                feature_id = rdflib.term.URIRef(kg_uri + f"lcms_feature_{usi}")

                g.add((feature_list, ns_kg.has_lcms_feature, feature_id))
                g.add((feature_id, RDF.type, ns_kg.LCMSFeature))
                g.add((feature_id, RDFS.label, rdflib.term.Literal(
                    f"lcms_feature {str(int(row['row ID']))} of LCMS feature list in {ionization_mode} ionization mode of {metadata.sample_id[0]}")))
                g.add((feature_id, ns_kg.has_ionization, rdflib.term.Literal(ionization_mode)))
                g.add((feature_id, ns_kg.has_row_id, rdflib.term.Literal(row['row ID'], datatype=XSD.integer)))
                g.add((feature_id, ns_kg.has_parent_mass, rdflib.term.Literal(row['row m/z'], datatype=XSD.float)))
                g.add((feature_id, ns_kg.has_retention_time, rdflib.term.Literal(row['row retention time'], datatype=XSD.float)))
                g.add((feature_id, ns_kg.has_feature_area, rdflib.term.Literal(row[area_col], datatype=XSD.float)))
                g.add((feature_id, ns_kg.has_relative_feature_area, rdflib.term.Literal(row[area_col]/max_area, datatype=XSD.float)))
                g.add((feature_id, ns_kg.has_usi, rdflib.term.Literal(usi)))
                link_spectrum = spectrum_dashboard_prefix + usi
                g.add((feature_id, ns_kg.gnps_dashboard_view, rdflib.URIRef(link_spectrum)))

                # add a fast Search link to the spectrum https://fasst.gnps2.org/fastsearch/ using the index and no analog search
                link_fast_search = gnps_fast_search_prefix + usi + '&library_select=gnpsdata_index&analog_select=No'
                g.add((feature_id, ns_kg.fast_search_gnpsdata_index_no_analog, rdflib.URIRef(link_fast_search)))

                # add a fast Search link to the spectrum https://fasst.gnps2.org/fastsearch/ using the index and analog search
                link_fast_search_analog = gnps_fast_search_prefix + usi + '&library_select=gnpsdata_index&analog_select=Yes'
                g.add((feature_id, ns_kg.fast_search_gnpsdata_index_analog, rdflib.URIRef(link_fast_search_analog)))

                # add a fast Search link to the spectrum https://fasst.gnps2.org/fastsearch/ using the GNPS library and no analog search
                link_fast_search_gnps_no_analog = gnps_fast_search_prefix + usi + '&library_select=gnpslibrary&analog_select=No'
                g.add((feature_id, ns_kg.fast_search_gnpslibrary_no_analog, rdflib.URIRef(link_fast_search_gnps_no_analog)))

                # add a fast Search link to the spectrum https://fasst.gnps2.org/fastsearch/ using the GNPS library and analog search
                link_fast_search_gnps_analog = gnps_fast_search_prefix + usi + '&library_select=gnpslibrary&analog_select=Yes'
                g.add((feature_id, ns_kg.fast_search_gnpslibrary_analog, rdflib.URIRef(link_fast_search_gnps_analog)))

                link_png = spectrum_png_prefix + usi
                g.add((feature_id, FOAF.depiction, rdflib.URIRef(link_png))) 
                
            # Serialize the graph
            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(os.path.join(pathout, f"features_{ionization_mode}.{output_format}"))
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            
            # Save parameters:
            params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
            
            if os.path.isfile(params_path):
                with open(params_path, encoding='UTF-8') as file:    
                    params_list = yaml.load(file, Loader=yaml.FullLoader) 
            else:
                params_list = {}
            print(f"Processed {directory}: RDF saved to {pathout}")

    except Exception as e:
        print(f"Error processing {directory}: {e}\n{traceback.format_exc()}")

# Parallelized main execution
if __name__ == "__main__":
    print(f"Processing directories in {sample_dir_path}")
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = list(tqdm(executor.map(process_directory, samples_dir), total=len(samples_dir), desc="Processing directories"))
