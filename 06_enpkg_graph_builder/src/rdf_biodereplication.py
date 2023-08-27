import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDFS, RDF, XSD
import sqlite3
from pathlib import Path
import argparse
import textwrap
from tqdm import tqdm

p = Path(__file__).parents[2]
os.chdir(p)


""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from a list of ChEMBL compounds
         --------------------------------
            Arguments:
            - Path to the SQL metadata DB with compounds' metadata
            - Path to the samples ChEMBL metadata FOLDER (will integrate all ChEMBL files)
            - Path to export the resulting .ttl file
        '''))

parser.add_argument('-chemdb', '--chem_metadata_path', required=True,
                    help='The path to the samples metadata SQL DB')
parser.add_argument('-biodb', '--bio_metadata_path', required=True,
                    help='The path to the samples ChEMBL metadata FOLDER (will integrate all ChEMBL files)')
parser.add_argument('-o', '--pathout', required=True,
                    help='The path to export the resulting .ttl file')

args = parser.parse_args()
pathout = os.path.normpath(args.pathout)
chem_metadata_path = os.path.normpath(args.chem_metadata_path)
path_bio = os.path.normpath(args.bio_metadata_path)

g = Graph()
nm = g.namespace_manager

# Create enpkg namespace
kg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(kg_uri)
prefix = "enpkg"
nm.bind(prefix, ns_kg)

# Create enpkgdemo namespace
demo_uri = "https://enpkg.commons-lab.org/module/"
ns_demo = rdflib.Namespace(demo_uri)
prefix = "enpkgmodule"
nm.bind(prefix, ns_demo)

compound_chembl_url = 'https://www.ebi.ac.uk/chembl/compound_report_card/'
target_chembl_url = 'https://www.ebi.ac.uk/chembl/target_report_card/'
assay_chembl_url = 'https://www.ebi.ac.uk/chembl/assay_report_card/'
document_chembl_url = 'https://www.ebi.ac.uk/chembl/document_report_card/'


metadata = []
for file in os.listdir(path_bio):
    if (file.startswith('CHEMBL')) and (file.endswith('.csv')):
        df_bio_metadata = pd.read_csv(path_bio + '/' + file, index_col=0)
        metadata.append(df_bio_metadata)
df_bio_metadata = pd.concat(metadata)

dat = sqlite3.connect(chem_metadata_path)
query = dat.execute("SELECT * From structures_metadata")
cols = [column[0] for column in query.description]
df_metadata = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)

i = 1
for _, row in tqdm(df_bio_metadata.iterrows(), total = len(df_bio_metadata)):
    inchikey = row['inchikey']
    uri_ik = rdflib.term.URIRef(kg_uri + inchikey)
    chembl_id_uri = rdflib.term.URIRef(compound_chembl_url + row['molecule_chembl_id'])
    target_id_uri = rdflib.term.URIRef(target_chembl_url + row['target_chembl_id'])
    assay_id_uri = rdflib.term.URIRef(assay_chembl_url + row['assay_chembl_id'])
    document_id_uri = rdflib.term.URIRef(document_chembl_url + row['document_chembl_id'])
    compound_activity_uri = rdflib.term.URIRef(demo_uri + 'chembl_activity_' + str(i))
    i += 1
    
    g.add((rdflib.term.URIRef(kg_uri + row['short_inchikey']), ns_kg.is_InChIkey2D_of, uri_ik))
    g.add((rdflib.term.URIRef(kg_uri + row['short_inchikey']), RDF.type, ns_kg.InChIkey2D)) 
    g.add((uri_ik, ns_demo.has_chembl_id, chembl_id_uri))    
    g.add((chembl_id_uri, ns_demo.has_chembl_activity, compound_activity_uri))
    g.add((target_id_uri, ns_demo.target_name, rdflib.term.Literal(row['target_pref_name'])))
    
    g.add((compound_activity_uri, ns_demo.target_id, target_id_uri))
    g.add((compound_activity_uri, ns_demo.assay_id, assay_id_uri))
    g.add((compound_activity_uri, ns_demo.target_name, rdflib.term.Literal(row['target_pref_name'])))
    g.add((compound_activity_uri, ns_demo.activity_type, rdflib.term.Literal(row['standard_type'])))
    g.add((compound_activity_uri, ns_demo.activity_relation, rdflib.term.Literal(row['standard_relation'])))
    g.add((compound_activity_uri, ns_demo.activity_value, rdflib.term.Literal(row['standard_value'], datatype=XSD.float)))
    g.add((compound_activity_uri, ns_demo.activity_unit, rdflib.term.Literal(row['standard_units'])))
    g.add((compound_activity_uri, ns_demo.stated_in_document, document_id_uri))
    g.add((document_id_uri, ns_demo.journal_name, rdflib.term.Literal(row['document_journal'])))
    g.add((compound_activity_uri, RDFS.label, rdflib.term.Literal(f"{row['standard_type']} of {row['molecule_chembl_id']} in assay {row['assay_chembl_id']} against {row['target_chembl_id']} ({row['target_pref_name']})")))

    g.add((target_id_uri, RDF.type, ns_demo.ChEMBLTarget))
    g.add((chembl_id_uri, RDF.type, ns_demo.ChEMBLChemical))
    g.add((document_id_uri, RDF.type, ns_demo.ChEMBLDocument))
    g.add((assay_id_uri, RDF.type, ns_demo.ChEMBLAssay))
    g.add((compound_activity_uri, RDF.type, ns_demo.ChEMBLAssayResults))

    if inchikey not in df_metadata['inchikey']:
        g.add((uri_ik, ns_kg.has_smiles, rdflib.term.Literal(row['isomeric_smiles'])))
        g.add((uri_ik, RDF.type, ns_kg.InChIkey))
        if (row['wikidata_id'] != 'no_wikidata_match') & (row['wikidata_id'] is not None):
            g.add((uri_ik, ns_kg.has_wd_id, rdflib.term.URIRef(row['wikidata_id'])))
            g.add((rdflib.term.URIRef(row['wikidata_id']), RDF.type, ns_kg.WDChemical))

g.serialize(destination=pathout, format="ttl", encoding="utf-8")
print(f'Result are in : {pathout}') 
