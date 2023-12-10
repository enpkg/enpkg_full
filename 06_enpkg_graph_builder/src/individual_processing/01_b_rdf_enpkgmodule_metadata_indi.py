import os
import argparse
import textwrap
import pandas as pd
import rdflib
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from pathlib import Path
from tqdm import tqdm
import git
import yaml
import sys

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


WD = Namespace(params_list_full['graph-builder']['wd_namespace'])

# Create enpkg namespace
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

# Create enpkgmodule namespace
module_uri = params_list_full['graph-builder']['module_uri']
ns_module = rdflib.Namespace(module_uri)
prefix_module = params_list_full['graph-builder']['prefix_module']

target_chembl_url = params_list_full['graph-builder']['target_chembl_url']

source_taxon_header = params_list_full['graph-builder']['source_taxon_header']
source_id_header = params_list_full['graph-builder']['source_id_header']



path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]



for directory in tqdm(samples_dir):
    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix, ns_kg)
    nm.bind(prefix_module, ns_module)

    try:

        metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
        try:
            metadata = pd.read_csv(metadata_path, sep='\t')
        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue
            
        sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])
        
        if metadata.sample_type[0] == 'sample':
            material_id = rdflib.term.URIRef(kg_uri + metadata[source_id_header][0])
            plant_parts = metadata[['organism_organe', 'organism_broad_organe', 'organism_tissue', 'organism_subsystem']].copy()
            plant_parts.fillna('unkown', inplace=True)
            plant_parts.replace(' ', '_', regex=True, inplace=True)
            
            g.add((material_id, ns_module.has_organe, rdflib.term.URIRef(module_uri + plant_parts['organism_organe'][0])))
            g.add((material_id, ns_module.has_broad_organe, rdflib.term.URIRef(module_uri + plant_parts['organism_broad_organe'][0])))
            g.add((material_id, ns_module.has_tissue, rdflib.term.URIRef(module_uri + plant_parts['organism_tissue'][0])))
            g.add((material_id, ns_module.has_subsystem, rdflib.term.URIRef(module_uri + plant_parts['organism_subsystem'][0])))
                    
            
            for assay_id, target, chembl_id, rdfclass in zip(
                ['bio_leish_donovani_10ugml_inhibition', 'bio_leish_donovani_2ugml_inhibition', 'bio_tryp_brucei_rhodesiense_10ugml_inhibition', \
                'bio_tryp_brucei_rhodesiense_2ugml_inhibition', 'bio_tryp_cruzi_10ugml_inhibition', 'bio_l6_cytotoxicity_10ugml_inhibition'], 
                ['Ldonovani_10ugml', 'Ldonovani_2ugml', 'Tbruceirhod_10ugml', 'Tbruceirhod_2ugml', 'Tcruzi_10ugml', 'L6_10ugml'],
                ['CHEMBL367', 'CHEMBL367', 'CHEMBL612348', 'CHEMBL612348', 'CHEMBL368', None],
                [ns_module.Ldono10ugml, ns_module.Ldono2ugml, ns_module.Tbrucei10ugml, ns_module.Tbrucei2ugml, ns_module.Tcruzi10ugml, ns_module.L610ugml]):    
                    
                    assay = rdflib.term.URIRef(module_uri + metadata.sample_id[0] + "_" + target)
                    type = rdflib.term.URIRef(module_uri + target)
                    g.add((sample, ns_module.has_bioassay_results, assay))
                    g.add((assay, RDFS.label, rdflib.term.Literal(f"{target} assay of {metadata.sample_id[0]}")))
                    g.add((assay, ns_module.inhibition_percentage, rdflib.term.Literal(metadata[assay_id][0], datatype=XSD.float)))
                    g.add((assay, RDF.type, rdfclass))
                    if chembl_id is not None:
                        target_id_uri = rdflib.term.URIRef(target_chembl_url + chembl_id)
                        g.add((assay, ns_module.target_id, target_id_uri))
                        g.add((target_id_uri, RDF.type, ns_module.ChEMBLTarget))

        pathout = os.path.join(sample_dir_path, directory, "rdf/")
        os.makedirs(pathout, exist_ok=True)
        pathout = os.path.normpath(os.path.join(pathout, f'metadata_module_enpkg.{output_format}'))
        
        if len(g)>0:
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            
            # Save parameters:
            params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
            
            if os.path.isfile(params_path):
                with open(params_path, encoding='UTF-8') as file:    
                    params_list = yaml.load(file, Loader=yaml.FullLoader) 
            else:
                params_list = {}  
                    
            # params_list.update({'metadata_module_enpkg':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
            #                     {'git_commit_link':f'https://github.com/enpkg/enpkg_full/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})


            # Retrieve the current Git commit hash
            git_commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha

            # Update params_list with version information in a dictionary format
            params_list['metadata_module_enpkg'] = {
                'git_commit': git_commit_hash,
                'git_commit_link': f'https://github.com/enpkg/enpkg_full/tree/{git_commit_hash}'
                }

            
            with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
                yaml.dump(params_list, file)
                
            print(f'Results are in : {pathout}')

    except KeyError as e:
        print(f'Error: {e} in {metadata_path} and directory {directory}')
        sys.exit(1)
            
