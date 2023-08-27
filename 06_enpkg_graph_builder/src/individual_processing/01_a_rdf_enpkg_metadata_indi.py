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

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from samples' ENPKG metadata 
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)

WD = Namespace('http://www.wikidata.org/entity/')
enpkg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(enpkg_uri)
prefix = "enpkg"

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]

for directory in tqdm(samples_dir):
    g = Graph()
    nm = g.namespace_manager
    nm.bind('wd', WD)
    nm.bind(prefix, ns_kg)

    metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
    try:
        metadata = pd.read_csv(metadata_path, sep='\t')
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
        
    sample = rdflib.term.URIRef(enpkg_uri + metadata.sample_id[0])
    
    if metadata.sample_type[0] == 'sample':
        material_id = rdflib.term.URIRef(enpkg_uri + metadata.source_id[0])
        g.add((material_id, RDF.type, ns_kg.RawMaterial))
        g.add((material_id, ns_kg.submitted_taxon, rdflib.term.Literal(metadata.source_taxon[0])))
        g.add((material_id, ns_kg.has_lab_process, sample))
        g.add((sample, RDF.type, ns_kg.LabExtract))
        g.add((sample, RDFS.label, rdflib.term.Literal(f"Sample {metadata.sample_id[0]}")))
        
        # Add GNPS Dashborad link for pos & neg: only if sample_filename_pos column exists and is not NaN and MassIVE id is present
        if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_pos'][0]):
                sample_filename_pos = metadata['sample_filename_pos'][0]
                massive_id = metadata['massive_id'][0]    
                gnps_dashboard_link = f'https://gnps-lcms.ucsd.edu/?usi=mzspec:{massive_id}:{sample_filename_pos}'
                gnps_tic_pic = f'https://gnps-lcms.ucsd.edu/mspreview?usi=mzspec:{massive_id}:{sample_filename_pos}'
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                
                for file in [directory for directory in os.listdir(os.path.join(path, directory, "pos"))]:
                    if file.startswith(f'{directory}_lcms_method_params_pos'):
                        lcms_analysis_params_path = os.path.join(path, directory, "pos", file)        

                hash_1 = get_hash(lcms_analysis_params_path)
                data_1 = get_data(lcms_analysis_params_path)
                has_lcms_hash = rdflib.term.URIRef(enpkg_uri + "has_LCMS_" + hash_1)
                g.add((sample, has_lcms_hash, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0])))
                g.add((has_lcms_hash, RDFS.subPropertyOf, rdflib.term.URIRef(enpkg_uri + 'has_LCMS')))
                g.add((has_lcms_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
                del(hash_1, data_1)
                
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_gnpslcms_link, rdflib.URIRef(gnps_dashboard_link)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), FOAF.depiction, rdflib.URIRef(gnps_tic_pic))) 
                
        if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_neg'][0]):
                sample_filename_neg = metadata['sample_filename_neg'][0]
                massive_id = metadata['massive_id'][0]    
                gnps_dashboard_link = f'https://gnps-lcms.ucsd.edu/?usi=mzspec:{massive_id}:{sample_filename_neg}'
                gnps_tic_pic = f'https://gnps-lcms.ucsd.edu/mspreview?usi=mzspec:{massive_id}:{sample_filename_neg}'
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                
                for file in [directory for directory in os.listdir(os.path.join(path, directory, "neg"))]:
                    if file.startswith(f'{directory}_lcms_method_params_neg'):
                        lcms_analysis_params_path = os.path.join(path, directory, "neg", file)        

                hash_1 = get_hash(lcms_analysis_params_path)
                data_1 = get_data(lcms_analysis_params_path)
                has_lcms_hash = rdflib.term.URIRef(enpkg_uri + "has_LCMS_" + hash_1)
                g.add((sample, has_lcms_hash, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0])))
                g.add((has_lcms_hash, RDFS.subPropertyOf, rdflib.term.URIRef(enpkg_uri + 'has_LCMS')))
                g.add((has_lcms_hash, ns_kg.has_content, rdflib.term.Literal(data_1)))
                del(hash_1, data_1)
            
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_gnpslcms_link, rdflib.URIRef(gnps_dashboard_link)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), FOAF.depiction, rdflib.URIRef(gnps_tic_pic))) 
           
        # Add WD taxonomy link to substance
        metadata_taxo_path = os.path.join(path, directory, 'taxo_output', directory + '_taxo_metadata.tsv')
        taxo_params_path = os.path.join(path, directory, 'taxo_output', 'params.yaml')
        try:
            metadata_taxo = pd.read_csv(metadata_taxo_path, sep='\t')
            if not pd.isna(metadata_taxo['wd.value'][0]):
                wd_id = rdflib.term.URIRef(WD + metadata_taxo['wd.value'][0][31:])               
                hash_2 = get_hash(taxo_params_path)
                data_2 = get_data(taxo_params_path)
                has_wd_id_hash = rdflib.term.URIRef(enpkg_uri + "has_wd_id_" + hash_2)
                g.add((material_id, has_wd_id_hash, wd_id))
                g.add((has_wd_id_hash, RDFS.subPropertyOf, rdflib.term.URIRef(enpkg_uri + 'has_wd_id')))
                g.add((has_wd_id_hash, ns_kg.has_content, rdflib.term.Literal(data_2)))
                g.add((wd_id, RDF.type, ns_kg.WDTaxon))
                del(hash_2, data_2)
                
            else:
                g.add((material_id, ns_kg.has_unresolved_taxon, rdflib.term.URIRef(enpkg_uri + 'unresolved_taxon')))              
        except FileNotFoundError:
            g.add((material_id, ns_kg.has_unresolved_taxon, rdflib.term.URIRef(enpkg_uri + 'unresolved_taxon')))
              
    elif metadata.sample_type[0] == 'blank':
        g.add((sample, RDF.type, ns_kg.LabBlank))
        g.add((sample, RDFS.label, rdflib.term.Literal(f"Blank {metadata.sample_id[0]}")))

        if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_pos'][0]):
                sample_filename_pos = metadata['sample_filename_pos'][0]
                massive_id = metadata['massive_id'][0]
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0])))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
        if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_neg'][0]):
                sample_filename_neg = metadata['sample_filename_neg'][0]
                massive_id = metadata['massive_id'][0]
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0])))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))


    elif metadata.sample_type[0] == 'qc':
        g.add((sample, RDF.type, ns_kg.LabQc))
        g.add((sample, RDFS.label, rdflib.term.Literal(f"QC {metadata.sample_id[0]}")))
        if set(['sample_filename_pos', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_pos'][0]):
                sample_filename_pos = metadata['sample_filename_pos'][0]
                massive_id = metadata['massive_id'][0]
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0])))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), RDF.type, ns_kg.LCMSAnalysisPos))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_pos'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))
        if set(['sample_filename_neg', 'massive_id']).issubset(metadata.columns):
            if not pd.isna(metadata['sample_filename_neg'][0]):
                sample_filename_neg = metadata['sample_filename_neg'][0]
                massive_id = metadata['massive_id'][0]
                link_to_massive = f'https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?accession={massive_id}'
                g.add((sample, ns_kg.has_LCMS, rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0])))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), RDF.type, ns_kg.LCMSAnalysisNeg))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_doi, rdflib.URIRef(link_to_massive)))
                g.add((rdflib.term.URIRef(enpkg_uri + metadata['sample_filename_neg'][0]), ns_kg.has_massive_license, rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/")))

    pathout = os.path.join(sample_dir_path, directory, "rdf/")
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.normpath(os.path.join(pathout, 'metadata_enpkg.ttl'))
    g.serialize(destination=pathout, format="ttl", encoding="utf-8")
    
    # Save parameters:
    params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
    
    if os.path.isfile(params_path):
        with open(params_path, encoding='UTF-8') as file:    
            params_list = yaml.load(file, Loader=yaml.FullLoader) 
    else:
        params_list = {}  
              
    params_list.update({'metadata_enpkg':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                        {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})
    
    with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
        yaml.dump(params_list, file)
    
    print(f'Results are in : {pathout}')
