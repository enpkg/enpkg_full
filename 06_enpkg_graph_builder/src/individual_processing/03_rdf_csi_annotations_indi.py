import os
import argparse
import json
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
ionization_mode = params_list_full['graph-builder']['ionization_mode']

g = Graph()
nm = g.namespace_manager

with open(os.path.normpath('data/adducts_formatter.json')) as json_file:
    adducts_dic = json.load(json_file)

kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

nm.bind(prefix, ns_kg)

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]
df_list = []
for directory in tqdm(samples_dir):
    g = Graph()
    nm = g.namespace_manager

    csi_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'compound_identifications.tsv')
    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        csi_annotations = pd.read_csv(csi_path, sep='\t')
        metadata = pd.read_csv(metadata_path, sep='\t')
        csi_annotations.replace({"adduct": adducts_dic},inplace=True)
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    for _, row in csi_annotations.iterrows():
        feature_id_int = row['id'].rsplit('_', 1)[1]
        # feature_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_feature_" + str(feature_id_int) + '_' + ionization_mode)
        # sirius_annotation_id = rdflib.term.URIRef(kg_uri + metadata.sample_id[0] + "_sirius_annotation_" + str(feature_id_int)  + '_' + ionization_mode)
        
        usi = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode+ '.mgf:scan:' + str(int(feature_id_int))
        feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi)
        sirius_annotation_id = rdflib.term.URIRef(kg_uri + "sirius_" + usi)
        
        InChIkey2D = rdflib.term.URIRef(kg_uri + row['InChIkey2D'])
        
        sirius_params_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'params.yml')
        hash_1 = get_hash(sirius_params_path)
        data_1 = get_data(sirius_params_path)
        has_sirius_annotation_hash = rdflib.term.URIRef(kg_uri + "has_sirius_annotation_" + hash_1)
        g.add((feature_id, has_sirius_annotation_hash, sirius_annotation_id))
        g.add((has_sirius_annotation_hash, RDFS.subPropertyOf, rdflib.term.URIRef(kg_uri + 'has_sirius_annotation')))
        g.add((has_sirius_annotation_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
        del(hash_1, data_1)
        
        g.add((sirius_annotation_id, ns_kg.has_InChIkey2D, InChIkey2D))
        g.add((sirius_annotation_id, ns_kg.has_ionization, rdflib.term.Literal(ionization_mode)))
        g.add((sirius_annotation_id, RDFS.label, rdflib.term.Literal(f"sirius annotation of {usi}")))
        #g.add((feature_id, ns_kg.has_annotation, InChIkey2D))
        g.add((sirius_annotation_id, ns_kg.has_sirius_adduct, rdflib.term.Literal(row['adduct'])))
        g.add((sirius_annotation_id, ns_kg.has_sirius_score, rdflib.term.Literal(row['SiriusScore'], datatype=XSD.float)))
        g.add((sirius_annotation_id, ns_kg.has_zodiac_score, rdflib.term.Literal(row['ZodiacScore'], datatype=XSD.float)))
        g.add((sirius_annotation_id, ns_kg.has_cosmic_score, rdflib.term.Literal(row['ConfidenceScore'], datatype=XSD.float)))       
        g.add((InChIkey2D, RDF.type, ns_kg.InChIkey2D))
        g.add((sirius_annotation_id, RDF.type, ns_kg.SiriusStructureAnnotation))

        
    pathout = os.path.join(sample_dir_path, directory, "rdf/")
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.normpath(os.path.join(pathout, f'sirius_{ionization_mode}.{output_format}'))
    g.serialize(destination=pathout, format=output_format, encoding="utf-8")
    
    # Save parameters:
    params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
    
    if os.path.isfile(params_path):
        with open(params_path, encoding='UTF-8') as file:    
            params_list = yaml.load(file, Loader=yaml.FullLoader) 
    else:
        params_list = {}  
            
    params_list.update({f'sirius_{ionization_mode}':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                        {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})
    
    with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
        yaml.dump(params_list, file)
        
    print(f'Results are in : {pathout}')
    