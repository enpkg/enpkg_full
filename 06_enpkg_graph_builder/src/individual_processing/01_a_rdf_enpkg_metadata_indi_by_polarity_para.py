import os
from pathlib import Path
import pandas as pd
import sys
import yaml
from rdflib import Graph, Namespace, RDF, RDFS, FOAF, Literal
from concurrent.futures import ProcessPoolExecutor
import traceback
from tqdm import tqdm

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

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


# Load parameters and substitute variables
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    sys.exit(1)

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

# Apply variable substitution
params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
ionization_mode = params_list_full['general']['polarity']  # Use this to filter for polarity
WD = Namespace(params_list_full['graph-builder']['wd_namespace'])
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
gnps_dashboard_prefix = params_list_full['graph-builder']['gnps_dashboard_prefix']
gnps_tic_pic_prefix = params_list_full['graph-builder']['gnps_tic_pic_prefix']
massive_prefix = params_list_full['graph-builder']['massive_prefix']
source_taxon_header = params_list_full['graph-builder']['source_taxon_header']
source_id_header = params_list_full['graph-builder']['source_id_header']

print(f"Resolved sample_dir_path: {sample_dir_path}")

# Validate the sample directory path
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    sys.exit(1)

samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]

def process_directory(directory):
    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix, ns_kg)

    try:
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")
        metadata = pd.read_csv(metadata_path, sep='\t', engine='python')

        sample = Namespace(kg_uri)[metadata.sample_id[0]]

        if metadata.sample_type[0] == 'sample':
            material_id = Namespace(kg_uri)[metadata[source_id_header][0]]
            g.add((material_id, RDF.type, ns_kg.RawMaterial))
            g.add((material_id, ns_kg.submitted_taxon, Literal(metadata[source_taxon_header][0])))
            g.add((material_id, ns_kg.has_lab_process, sample))
            g.add((sample, RDF.type, ns_kg.LabExtract))
            g.add((sample, RDFS.label, Literal(f"Sample {metadata.sample_id[0]}")))

            # Handle only the specified ionization mode
            if ionization_mode in ['pos', 'neg']:
                if set([f'sample_filename_{ionization_mode}', 'massive_id']).issubset(metadata.columns):
                    filename = metadata[f'sample_filename_{ionization_mode}'][0]
                    if not pd.isna(filename):
                        massive_id = metadata['massive_id'][0]
                        gnps_dashboard_link = f"{gnps_dashboard_prefix}{massive_id}:{filename}"
                        gnps_tic_pic = f"{gnps_tic_pic_prefix}{massive_id}:{filename}"
                        link_to_massive = f"{massive_prefix}{massive_id}"

                        lcms_method_params_path = None
                        for file in os.listdir(os.path.join(sample_dir_path, directory, ionization_mode)):
                            if file.startswith(f"{directory}_lcms_method_params_{ionization_mode}"):
                                lcms_method_params_path = os.path.join(sample_dir_path, directory, ionization_mode, file)
                                break

                        if lcms_method_params_path:
                            hash_1 = get_hash(lcms_method_params_path)
                            data_1 = get_data(lcms_method_params_path)
                            has_lcms_hash = Namespace(kg_uri)[f"has_LCMS_{hash_1}"]
                            g.add((sample, has_lcms_hash, Namespace(kg_uri)[filename]))
                            g.add((has_lcms_hash, RDFS.subPropertyOf, Namespace(kg_uri).has_LCMS))
                            g.add((has_lcms_hash, ns_kg.has_content, Literal(data_1)))
                            del hash_1, data_1

                        g.add((Namespace(kg_uri)[filename], RDF.type, getattr(ns_kg, f"LCMSAnalysis{ionization_mode.capitalize()}")))
                        g.add((Namespace(kg_uri)[filename], ns_kg.has_gnpslcms_link, Literal(gnps_dashboard_link)))
                        g.add((Namespace(kg_uri)[filename], ns_kg.has_massive_doi, Literal(link_to_massive)))
                        g.add((Namespace(kg_uri)[filename], ns_kg.has_massive_license, Literal("https://creativecommons.org/publicdomain/zero/1.0/")))
                        g.add((Namespace(kg_uri)[filename], FOAF.depiction, Literal(gnps_tic_pic)))
            # Add WD taxonomy link to substance
            metadata_taxo_path = os.path.join(sample_dir_path, directory, 'taxo_output', f"{directory}_taxo_metadata.tsv")
            taxo_params_path = os.path.join(sample_dir_path, directory, 'taxo_output', 'params.yaml')
            try:
                metadata_taxo = pd.read_csv(metadata_taxo_path, sep='\t')
                if not pd.isna(metadata_taxo['wd.value'][0]):
                    wd_id = Namespace(WD)[metadata_taxo['wd.value'][0][31:]]               
                    hash_2 = get_hash(taxo_params_path)
                    data_2 = get_data(taxo_params_path)
                    has_wd_id_hash = Namespace(kg_uri)[f"has_wd_id_{hash_2}"]
                    g.add((material_id, has_wd_id_hash, wd_id))
                    g.add((has_wd_id_hash, RDFS.subPropertyOf, Namespace(kg_uri).has_wd_id))
                    g.add((has_wd_id_hash, ns_kg.has_content, Literal(data_2)))
                    g.add((wd_id, RDF.type, ns_kg.WDTaxon))
                    del hash_2, data_2
                else:
                    g.add((material_id, ns_kg.has_unresolved_taxon, Namespace(kg_uri).unresolved_taxon))              
            except FileNotFoundError:
                g.add((material_id, ns_kg.has_unresolved_taxon, Namespace(kg_uri).unresolved_taxon))

        elif metadata.sample_type[0] == 'blank':
            g.add((sample, RDF.type, ns_kg.LabBlank))
            g.add((sample, RDFS.label, Literal(f"Blank {metadata.sample_id[0]}")))

            if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'pos':
                if not pd.isna(metadata['sample_filename_pos'][0]):
                    sample_filename_pos = metadata['sample_filename_pos'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f"{massive_prefix}{massive_id}"
                    g.add((sample, ns_kg.has_LCMS, Namespace(kg_uri)[sample_filename_pos]))
                    g.add((Namespace(kg_uri)[sample_filename_pos], RDF.type, ns_kg.LCMSAnalysisPos))
                    g.add((Namespace(kg_uri)[sample_filename_pos], ns_kg.has_massive_doi, Literal(link_to_massive)))
                    g.add((Namespace(kg_uri)[sample_filename_pos], ns_kg.has_massive_license, Literal("https://creativecommons.org/publicdomain/zero/1.0/")))

            if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'neg':
                if not pd.isna(metadata['sample_filename_neg'][0]):
                    sample_filename_neg = metadata['sample_filename_neg'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f"{massive_prefix}{massive_id}"
                    g.add((sample, ns_kg.has_LCMS, Namespace(kg_uri)[sample_filename_neg]))
                    g.add((Namespace(kg_uri)[sample_filename_neg], RDF.type, ns_kg.LCMSAnalysisNeg))
                    g.add((Namespace(kg_uri)[sample_filename_neg], ns_kg.has_massive_doi, Literal(link_to_massive)))
                    g.add((Namespace(kg_uri)[sample_filename_neg], ns_kg.has_massive_license, Literal("https://creativecommons.org/publicdomain/zero/1.0/")))

        elif metadata.sample_type[0] == 'qc':
            g.add((sample, RDF.type, ns_kg.LabQc))
            g.add((sample, RDFS.label, Literal(f"QC {metadata.sample_id[0]}")))

            if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'pos':
                if not pd.isna(metadata['sample_filename_pos'][0]):
                    sample_filename_pos = metadata['sample_filename_pos'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f"{massive_prefix}{massive_id}"
                    g.add((sample, ns_kg.has_LCMS, Namespace(kg_uri)[sample_filename_pos]))
                    g.add((Namespace(kg_uri)[sample_filename_pos], RDF.type, ns_kg.LCMSAnalysisPos))
                    g.add((Namespace(kg_uri)[sample_filename_pos], ns_kg.has_massive_doi, Literal(link_to_massive)))
                    g.add((Namespace(kg_uri)[sample_filename_pos], ns_kg.has_massive_license, Literal("https://creativecommons.org/publicdomain/zero/1.0/")))

            if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'neg':
                if not pd.isna(metadata['sample_filename_neg'][0]):
                    sample_filename_neg = metadata['sample_filename_neg'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f"{massive_prefix}{massive_id}"
                    g.add((sample, ns_kg.has_LCMS, Namespace(kg_uri)[sample_filename_neg]))
                    g.add((Namespace(kg_uri)[sample_filename_neg], RDF.type, ns_kg.LCMSAnalysisNeg))
                    g.add((Namespace(kg_uri)[sample_filename_neg], ns_kg.has_massive_doi, Literal(link_to_massive)))
                    g.add((Namespace(kg_uri)[sample_filename_neg], ns_kg.has_massive_license, Literal("https://creativecommons.org/publicdomain/zero/1.0/")))


        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.join(pathout, f"metadata_enpkg_{ionization_mode}.{output_format}")
        g.serialize(destination=pathout, format=output_format, encoding="utf-8")
        print(f"Results are in: {pathout}")

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message

def main():
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = list(tqdm(executor.map(process_directory, samples_dir), total=len(samples_dir)))
        for result in results:
            if isinstance(result, str) and "Error processing" in result:
                print("Stopping script due to an error in a worker process.")
                executor.shutdown(wait=False)
                sys.exit(1)

if __name__ == "__main__":
    main()
