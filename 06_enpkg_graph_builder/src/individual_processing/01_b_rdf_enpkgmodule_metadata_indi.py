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

p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from samples' MODULE metadata 
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)

WD = Namespace('http://www.wikidata.org/entity/')

# Create enpkg namespace
kg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(kg_uri)
prefix_kg = "enpkg"

# Create enpkgmodule namespace
module_uri = "https://enpkg.commons-lab.org/module/"
ns_module = rdflib.Namespace(module_uri)
prefix_module = "enpkgmodule"

target_chembl_url = 'https://www.ebi.ac.uk/chembl/target_report_card/'

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]


for directory in tqdm(samples_dir):
    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix_kg, ns_kg)
    nm.bind(prefix_module, ns_module)

    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
        
    sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])
    
    if metadata.sample_type[0] == 'sample':
        material_id = rdflib.term.URIRef(kg_uri + metadata.source_id[0])
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
    pathout = os.path.normpath(os.path.join(pathout, 'metadata_module_enpkg.ttl'))
    
    if len(g)>0:
        g.serialize(destination=pathout, format="ttl", encoding="utf-8")
        
        # Save parameters:
        params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
        
        if os.path.isfile(params_path):
            with open(params_path, encoding='UTF-8') as file:    
                params_list = yaml.load(file, Loader=yaml.FullLoader) 
        else:
            params_list = {}  
                
        params_list.update({'metadata_module_enpkg':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                            {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})
        
        with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
            yaml.dump(params_list, file)
            
        print(f'Results are in : {pathout}')          
        
