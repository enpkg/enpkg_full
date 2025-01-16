import os
from pathlib import Path
import argparse
import textwrap
import pandas as pd
import rdflib
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, FOAF
from tqdm import tqdm
import sys
import yaml
import git
from concurrent.futures import ProcessPoolExecutor
import traceback

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

p = Path(__file__).parents[2]
os.chdir(p)

# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['graph-builder']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']


sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
output_format = params_list_full['graph-builder']['graph_format']
ionization_mode = params_list_full['general']['polarity']


WD = Namespace(params_list_full['graph-builder']['wd_namespace'])
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
gnps_dashboard_prefix = params_list_full['graph-builder']['gnps_dashboard_prefix']
gnps_tic_pic_prefix = params_list_full['graph-builder']['gnps_tic_pic_prefix']
massive_prefix = params_list_full['graph-builder']['massive_prefix']

source_taxon_header = params_list_full['graph-builder']['source_taxon_header']
source_id_header = params_list_full['graph-builder']['source_id_header']

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]

#For debugging only !!!
# directory = 'VGF151_E05'

def process_directory(directory):

    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix, ns_kg)

    try:

        metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
        metadata = pd.read_csv(metadata_path, sep='\t')

        sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])
        
        if metadata.sample_type[0] == 'sample':
            material_id = rdflib.term.URIRef(kg_uri + metadata[source_id_header][0])
            g.add((material_id, RDF.type, ns_kg.RawMaterial))
            g.add((material_id, ns_kg.submitted_taxon, rdflib.term.Literal(metadata[source_taxon_header][0])))
            g.add((material_id, ns_kg.has_lab_process, sample))
            g.add((sample, RDF.type, ns_kg.LabExtract))
            g.add((sample, RDFS.label, rdflib.term.Literal(f"Sample {metadata.sample_id[0]}")))
            
            # Add GNPS Dashboard link for pos & neg: only if sample_filename_pos column exists and is not NaN and MassIVE id is present
            if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'pos':
                if not pd.isna(metadata['sample_filename_pos'][0]):
                    sample_filename_pos = metadata['sample_filename_pos'][0]
                    massive_id = metadata['massive_id'][0]
                    gnps_dashboard_link = f'{gnps_dashboard_prefix}{massive_id}:{sample_filename_pos}'
                    gnps_tic_pic = f'{gnps_tic_pic_prefix}{massive_id}:{sample_filename_pos}'
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    
                    for file in [directory for directory in os.listdir(os.path.join(path, directory, "pos"))]:
                        if file.startswith(f'{directory}_lcms_method_params_pos'):
                            lcms_analysis_params_path = os.path.join(path, directory, "pos", file)        

                    hash_1 = get_hash(lcms_analysis_params_path)
                    data_1 = get_data(lcms_analysis_params_path)
                    has_lcms_hash = rdflib.term.URIRef(kg_uri + "has_LCMS_" + hash_1)
                    g.add((sample, has_lcms_hash, rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0])))
                    g.add((has_lcms_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_LCMS')))
                    g.add((has_lcms_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
                    del(hash_1, data_1)
                    
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_gnpslcms_link, rdflib.URIRef(gnps_dashboard_link)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), FOAF.depiction, rdflib.URIRef(gnps_tic_pic))) 
                    
            if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'neg':
                if not pd.isna(metadata['sample_filename_neg'][0]):
                    sample_filename_neg = metadata['sample_filename_neg'][0]
                    massive_id = metadata['massive_id'][0]    
                    gnps_dashboard_link = f'{gnps_dashboard_prefix}{massive_id}:{sample_filename_neg}'
                    gnps_tic_pic = f'{gnps_tic_pic_prefix}{massive_id}:{sample_filename_neg}'
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    
                    for file in [directory for directory in os.listdir(os.path.join(path, directory, "neg"))]:
                        if file.startswith(f'{directory}_lcms_method_params_neg'):
                            lcms_analysis_params_path = os.path.join(path, directory, "neg", file)        

                    hash_1 = get_hash(lcms_analysis_params_path)
                    data_1 = get_data(lcms_analysis_params_path)
                    has_lcms_hash = rdflib.term.URIRef(kg_uri + "has_LCMS_" + hash_1)
                    g.add((sample, has_lcms_hash, rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0])))
                    g.add((has_lcms_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_LCMS')))
                    g.add((has_lcms_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
                    del(hash_1, data_1)
                
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_gnpslcms_link, rdflib.URIRef(gnps_dashboard_link)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), FOAF.depiction, rdflib.URIRef(gnps_tic_pic))) 
            
            # Add WD taxonomy link to substance
            metadata_taxo_path = os.path.join(path, directory, 'taxo_output', directory + '_taxo_metadata.tsv')
            taxo_params_path = os.path.join(path, directory, 'taxo_output', 'params.yaml')
            try:
                metadata_taxo = pd.read_csv(metadata_taxo_path, sep='\t')
                if not pd.isna(metadata_taxo['wd.value'][0]):
                    wd_id = rdflib.term.URIRef(WD + metadata_taxo['wd.value'][0][31:])               
                    hash_2 = get_hash(taxo_params_path)
                    data_2 = get_data(taxo_params_path)
                    has_wd_id_hash = rdflib.term.URIRef(kg_uri + "has_wd_id_" + hash_2)
                    g.add((material_id, has_wd_id_hash, wd_id))
                    g.add((has_wd_id_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_wd_id')))
                    g.add((has_wd_id_hash, ns_kg.has_content, rdflib.term.Literal(data_2)))
                    g.add((wd_id, RDF.type, ns_kg.WDTaxon))
                    del(hash_2, data_2)
                    
                else:
                    g.add((material_id, ns_kg.has_unresolved_taxon, rdflib.term.URIRef(kg_uri + 'unresolved_taxon')))              
            except FileNotFoundError:
                g.add((material_id, ns_kg.has_unresolved_taxon, rdflib.term.URIRef(kg_uri + 'unresolved_taxon')))
                
        elif metadata.sample_type[0] == 'blank':
            g.add((sample, RDF.type, ns_kg.LabBlank))
            g.add((sample, RDFS.label, rdflib.term.Literal(f"Blank {metadata.sample_id[0]}")))

            if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'pos':
                if not pd.isna(metadata['sample_filename_pos'][0]):
                    sample_filename_pos = metadata['sample_filename_pos'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0])))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
            if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'neg':
                if not pd.isna(metadata['sample_filename_neg'][0]):
                    sample_filename_neg = metadata['sample_filename_neg'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0])))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))


        elif metadata.sample_type[0] == 'qc':
            g.add((sample, RDF.type, ns_kg.LabQc))
            g.add((sample, RDFS.label, rdflib.term.Literal(f"QC {metadata.sample_id[0]}")))
            if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'pos':
                if not pd.isna(metadata['sample_filename_pos'][0]):
                    sample_filename_pos = metadata['sample_filename_pos'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0])))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
            if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns) and ionization_mode == 'neg':
                if not pd.isna(metadata['sample_filename_neg'][0]):
                    sample_filename_neg = metadata['sample_filename_neg'][0]
                    massive_id = metadata['massive_id'][0]
                    link_to_massive = f'{massive_prefix}{massive_id}'
                    g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0])))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                    g.add((rdflib.term.URIRef(kg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))

        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.normpath(os.path.join(pathout, f'metadata_enpkg.{output_format}'))
        g.serialize(destination=pathout, format=output_format, encoding="utf-8")
        
        # Save parameters:
        params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
        
        if os.path.isfile(params_path):
            with open(params_path, encoding='UTF-8') as file:    
                params_list = yaml.load(file, Loader=yaml.FullLoader) 
        else:
            params_list = {}  
                
        # params_list.update({'metadata_enpkg':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
        #                     {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})

        # Retrieve the current Git commit hash
        git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha

        # Update params_list with version information in a dictionary format
        params_list['metadata_enpkg'] = {
            'git_commit': git_commit_hash,
            'git_commit_link': f'https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}'
            }
        
        with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
            yaml.dump(params_list, file)
        
        print(f'Results are in : {pathout}')


    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message


# The main portion of your script would then use a ProcessPoolExecutor
# to process multiple directories in parallel.

# Assuming 'path' is the directory where all your sample directories are located

path = os.path.normpath(sample_dir_path)

samples_dir = [directory for directory in os.listdir(path) if not directory.startswith('.')]

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
