import os
import yaml
import argparse
import textwrap
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from pathlib import Path
from tqdm import tqdm
import sys
import yaml
import git
from concurrent.futures import ProcessPoolExecutor
import traceback
from concurrent.futures import as_completed


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

greek_alphabet = 'ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩωÎ²Iµ'
latin_alphabet = 'AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtUuFfQqYyWwI2Iu'
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)



g = Graph()
nm = g.namespace_manager
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
nm.bind(prefix, ns_kg)

# # For debug purposes only !!!
# directory = 'VGF138_A02'

def process_directory(directory):

    g = Graph()
    nm = g.namespace_manager
    nm.bind(prefix, ns_kg)
        
    sirius_param_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'params.yml')
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')


    try:

        metadata = pd.read_csv(metadata_path, sep='\t')

        if not os.path.exists(sirius_param_path) or not os.path.exists(metadata_path):
            print(f'No params.yml or metadata.tsv for {directory}')
        
        # We skip if the sample is of type QC or Blank
        if metadata.sample_type[0] == 'QC' or metadata.sample_type[0] == 'Blank':
            print(f'Skipping {directory}, QC or Blank sample.')
            return f'Skipped {directory} due to QC or Blank sample.'

        elif metadata.sample_type[0] == 'sample':

            with open (sirius_param_path) as file:    
                params_list = yaml.load(file, Loader=yaml.FullLoader)
            sirius_version = params_list['options']['sirius_version']
            
            if sirius_version == 4:
                # Canopus NPC results integration for sirius 4
                try:
                    canopus_npc_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'npc_summary.csv')
                    canopus_annotations = pd.read_csv(canopus_npc_path, encoding="utf-8")
                    canopus_annotations = canopus_annotations.fillna('Unknown')
                    for _, row in canopus_annotations.iterrows():        
                        # feature_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_feature_" + str(row['name']) + '_' + ionization_mode)
                        # canopus_annotation_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_canopus_annotation_" + str(row['name'])+ '_' + ionization_mode)
                        
                        usi = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode+ '.mgf:scan:' + str(row['name'])
                        feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi)
                        canopus_annotation_id = rdflib.term.URIRef(kg_uri + "canopus_" + usi)
                        
                        npc_pathway = rdflib.term.URIRef(kg_uri + "npc_" + row['pathway'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        npc_superclass = rdflib.term.URIRef(kg_uri + "npc_" + row['superclass'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        npc_class = rdflib.term.URIRef(kg_uri + "npc_" + row['class'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        
                        g.add((npc_pathway, RDF.type, ns_kg.NPCPathway))
                        g.add((npc_superclass, RDF.type, ns_kg.NPCSuperclass))
                        g.add((npc_class, RDF.type, ns_kg.NPCClass))
                        
                        sirius_params_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'params.yml')
                        hash_1 = get_hash(sirius_params_path)
                        data_1 = get_data(sirius_params_path)
                        has_canopus_annotation_hash = rdflib.term.URIRef(kg_uri + "has_canopus_annotation_" + hash_1)
                        g.add((feature_id, has_canopus_annotation_hash, canopus_annotation_id))
                        g.add((has_canopus_annotation_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_canopus_annotation')))
                        g.add((has_canopus_annotation_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
                        del(hash_1, data_1)
                
                        g.add((canopus_annotation_id, RDFS.label, rdflib.term.Literal(f"canopus annotation of {usi}")))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway, npc_pathway))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway_prob, rdflib.term.Literal(row['pathwayProbability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass, npc_superclass))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass_prob, rdflib.term.Literal(row['superclassProbability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class, npc_class))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class_prob, rdflib.term.Literal(row['classProbability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, RDF.type, ns_kg.SiriusCanopusAnnotation))

                except Exception as e:
                    error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
                    print(error_message)
                    return error_message
                
            elif sirius_version in (5, 6):
                # Canopus NPC results integration for sirius 5
                try:
                    canopus_dir = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS')
                    canopus_candidates = [
                        os.path.join(canopus_dir, 'canopus_compound_summary.tsv'),
                        os.path.join(canopus_dir, 'canopus_structure_summary.tsv')
                    ]
                    canopus_npc_path = next((f for f in canopus_candidates if os.path.exists(f)), None)
                    if canopus_npc_path is None:
                        raise FileNotFoundError('No CANOPUS summary file found (expected canopus_compound_summary.tsv or canopus_structure_summary.tsv)')
                    canopus_annotations = pd.read_csv(canopus_npc_path, sep='\t', encoding="utf-8")
                    canopus_annotations = canopus_annotations.fillna('Unknown')
                    for _, row in canopus_annotations.iterrows():
                        
                        feature_identifier = row.get('id')
                        if isinstance(feature_identifier, str):
                            feature_id_raw = feature_identifier.rsplit('_', 1)[1]
                        else:
                            mapping_id = row.get('mappingFeatureId')
                            if pd.isna(mapping_id):
                                raise KeyError("No feature identifier column ('id' or 'mappingFeatureId') in CANOPUS summary.")
                            feature_id_raw = str(mapping_id)
                        # canopus_annotation_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_canopus_annotation_" + str(feature_id)+ '_' + ionization_mode)                
                        # feature_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_feature_" + str(feature_id)+ '_' + ionization_mode)             
                        usi = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode+ '.mgf:scan:' + str(feature_id_raw)
                        feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi)
                        canopus_annotation_id = rdflib.term.URIRef(kg_uri + "canopus_" + usi)
                        
                        npc_pathway = rdflib.term.URIRef(kg_uri + "npc_" + row['NPC#pathway'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        npc_superclass = rdflib.term.URIRef(kg_uri + "npc_" + row['NPC#superclass'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        npc_class = rdflib.term.URIRef(kg_uri + "npc_" + row['NPC#class'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin))
                        
                        g.add((npc_pathway, RDF.type, ns_kg.NPCPathway))
                        g.add((npc_superclass, RDF.type, ns_kg.NPCSuperclass))
                        g.add((npc_class, RDF.type, ns_kg.NPCClass))
                        
                        g.add((feature_id, ns_kg.has_canopus_annotation, canopus_annotation_id))
                        g.add((canopus_annotation_id, RDFS.label, rdflib.term.Literal(f"canopus annotation of {usi}")))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway, npc_pathway))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway_prob, rdflib.term.Literal(row['NPC#pathway Probability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass, npc_superclass))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass_prob, rdflib.term.Literal(row['NPC#superclass Probability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class, npc_class))
                        g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class_prob, rdflib.term.Literal(row['NPC#class Probability'], datatype=XSD.float)))
                        g.add((canopus_annotation_id, RDF.type, ns_kg.SiriusCanopusAnnotation))
                
                except Exception as e:
                    error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
                    print(error_message)
                    return error_message
                
            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(os.path.join(pathout, f'canopus_{ionization_mode}.{output_format}'))
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            
            # Save parameters:
            params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
            
            if os.path.isfile(params_path):
                with open(params_path, encoding='UTF-8') as file:    
                    params_list = yaml.load(file, Loader=yaml.FullLoader)
            # here we make sure to make and empty dictionary if the file exists but is empty
            elif os.path.isfile(params_path) and os.path.getsize(params_path) == 0:
                params_list = {}
            else:
                params_list = {}  
                    
            # params_list.update({f'canopus_{ionization_mode}':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
            #                     {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})

            # Retrieve the current Git commit hash
            git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha


            # Update params_list with version information in a dictionary format
            params_list[f'canopus_{ionization_mode}'] = {
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
df_list = []

def main():
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, samples_dir)
        # for result in results:
        #     if isinstance(result, str) and "Error processing" in result:
        #         print("Stopping script due to an error in a worker process.")
        #         executor.shutdown(wait=False)  # Stop all running workers
        #         sys.exit(1)  # Exit the main script

# Ensure running main function when the script is executed
if __name__ == "__main__":
    main()
