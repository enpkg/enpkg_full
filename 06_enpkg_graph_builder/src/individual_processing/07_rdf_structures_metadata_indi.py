import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS
import sqlite3
import argparse
import textwrap
from pathlib import Path
from tqdm import tqdm
import git
import yaml

# These lines allows to make sure that we are placed at the repo directory level 
p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from chemical structures metadata
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
            - Path to the SQL metadata DB with compounds' metadata
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')
parser.add_argument('-db', '--metadata_path', required=True,
                    help='The path to the structures metadata SQL DB')


args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
metadata_path = os.path.normpath(args.metadata_path)

greek_alphabet = 'ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩωÎ²Iµ'
latin_alphabet = 'AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtUuFfQqYyWwI2Iu'
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)

# Connect to structures DB
dat = sqlite3.connect(metadata_path)
query = dat.execute("SELECT * From structures_metadata")
cols = [column[0] for column in query.description]
df_metadata = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)

kg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(kg_uri)
prefix = "enpkg"

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]
df_list = []
for directory in tqdm(samples_dir):    
    
    paths = []
    isdb_pos_path = os.path.join(path, directory, 'rdf/isdb_pos.ttl')
    isdb_neg_path = os.path.join(path, directory, 'rdf/isdb_neg.ttl')
    sirius_pos_path = os.path.join(path, directory, 'rdf/sirius_pos.ttl')
    sirius_neg_path = os.path.join(path, directory, 'rdf/sirius_neg.ttl')

    paths = [isdb_pos_path, isdb_neg_path, sirius_pos_path, sirius_neg_path]
    path_exist = []
    for path_annot in paths:
        if os.path.isfile(path_annot):
            path_exist.append(path_annot)
        else:
            pass
    if len(path_exist) == 0:
        continue

    merged_graph = Graph()
    nm = merged_graph.namespace_manager
    nm.bind(prefix, ns_kg)
    for path_annot in path_exist:
        with open(path_annot, "r") as f:
            file_content = f.read()
            merged_graph.parse(data=file_content, format="ttl")
    
    sample_short_ik = []
    for s, p, o in merged_graph.triples((None,  RDF.type, ns_kg.InChIkey2D)):
        sample_short_ik.append(s[-14:])

    sample_specific_db = df_metadata[df_metadata['short_inchikey'].isin(sample_short_ik)]

    g = Graph()
    nm = g.namespace_manager
    nm.bind(prefix, ns_kg)   
    for _, row in sample_specific_db.iterrows():
        short_ik = rdflib.term.URIRef(kg_uri + row['short_inchikey'])
        npc_pathway_list = row['npc_pathway'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')
        npc_superclass_list = row['npc_superclass'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')
        npc_class_list = row['npc_class'].replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_").translate(greek2latin).split('|')

        npc_pathway_urilist = []
        npc_superclass_urilist = []
        npc_class_urilist = []

        for list, uri_list in zip([npc_pathway_list, npc_superclass_list, npc_class_list],
                                [npc_pathway_urilist, npc_superclass_urilist, npc_class_urilist]):
            for item in list:
                uri_list.append(rdflib.term.URIRef(kg_uri + "npc_" + item))
                    
        g.add((short_ik, ns_kg.has_smiles, rdflib.term.Literal(row['smiles'])))

        all_npc_pathway = []
        all_npc_superclass = []
        all_npc_class = []
        
        for uri in npc_pathway_urilist:
            g.add((short_ik, ns_kg.has_npc_pathway, uri))
            if uri not in all_npc_pathway:
                g.add((uri, RDF.type, ns_kg.NPCPathway))
                all_npc_pathway.append(uri)
        for uri in npc_superclass_urilist:
            g.add((short_ik, ns_kg.has_npc_superclass, uri))
            if uri not in all_npc_superclass:
                g.add((uri, RDF.type, ns_kg.NPCSuperclass))
                all_npc_superclass.append(uri)
        for uri in npc_class_urilist:
            g.add((short_ik, ns_kg.has_npc_class, uri))
            if uri not in all_npc_class:
                g.add((uri, RDF.type, ns_kg.NPCClass))
                all_npc_class.append(uri)
        
        if (row['wikidata_id'] != 'no_wikidata_match') & (row['wikidata_id'] != None):
            g.add((short_ik, ns_kg.is_InChIkey2D_of, rdflib.term.URIRef(kg_uri + row['inchikey'])))
            g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_wd_id, rdflib.term.URIRef(row['wikidata_id'])))
            g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), RDF.type, ns_kg.InChIkey))

            for uri in npc_pathway_urilist:
                g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_npc_pathway, uri))
            for uri in npc_superclass_urilist:
                g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_npc_superclass, uri))
            for uri in npc_class_urilist:
                g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_npc_class, uri))
                
            g.add((rdflib.term.URIRef(kg_uri + row['inchikey']), ns_kg.has_smiles, rdflib.term.Literal(row['isomeric_smiles'])))
            g.add((rdflib.term.URIRef(row['wikidata_id']), RDF.type, ns_kg.WDChemical))
                
    pathout = os.path.join(sample_dir_path, directory, "rdf/")
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.normpath(os.path.join(pathout, 'structures_metadata.ttl'))
    g.serialize(destination=pathout, format="ttl", encoding="utf-8")
    
    # Save parameters:
    params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
    
    if os.path.isfile(params_path):
        with open(params_path, encoding='UTF-8') as file:    
            params_list = yaml.load(file, Loader=yaml.FullLoader) 
    else:
        params_list = {}  
            
    params_list.update({'structures_metadata':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                        {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'},
                        {'db_structures_metadata':metadata_path}]})
    
    with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
        yaml.dump(params_list, file)
        
    print(f'Results are in : {pathout}')  
