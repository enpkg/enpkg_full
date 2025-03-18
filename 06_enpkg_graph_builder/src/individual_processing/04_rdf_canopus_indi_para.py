import os
import sys
import yaml
import traceback
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, XSD, Literal
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

sys.path.append(os.path.join(Path(__file__).parents[1], 'functions'))
from hash_functions import get_hash, get_data

def substitute_variables(config):
    """Recursively substitute placeholders in YAML."""
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
        "general.polarity": config["general"]["polarity"]
    }
    recurse_dict(config, context)
    return config

p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    raise FileNotFoundError('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list_full = substitute_variables(params_list_full)

sample_dir_path = os.path.normpath(params_list_full["general"]["treated_data_path"])
output_format = params_list_full["graph-builder"]["graph_format"]
ionization_mode = params_list_full["general"]["polarity"]
sirius_version = params_list_full["sirius"]["options"]["sirius_version"]

kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']

greek_alphabet = 'ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩωÎ²Iµ'
latin_alphabet = 'AaBbGgDdEeZzHhJjIiKkLlMmNnXxOoPpRrSssTtUuFfQqYyWwI2Iu'
greek2latin = str.maketrans(greek_alphabet, latin_alphabet)

def safe_translate(text, mapping):
    return text.translate(mapping) if isinstance(text, str) else 'Unknown'

if not os.path.exists(sample_dir_path):
    raise FileNotFoundError(f"Sample directory path not found: {sample_dir_path}")

def process_directory(directory):
    g = Graph()
    g.namespace_manager.bind(prefix, ns_kg)
    
    try:
        sirius_param_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_WORKSPACE_SIRIUS", "params.yml")
        metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

        if not os.path.exists(sirius_param_path) or not os.path.exists(metadata_path):
            print(f"No params.yml or metadata.tsv for {directory}")
            return

        metadata = pd.read_csv(metadata_path, sep="\t")
        if metadata.empty or 'sample_type' not in metadata.columns:
            print(f"Metadata file missing required columns for {directory}")
            return

        if metadata.sample_type[0] in ['QC', 'Blank']:
            return

        print(f"Processing sample: {directory}")

        if sirius_version == 4:
            try:
                canopus_npc_path = os.path.join(sample_dir_path, directory, ionization_mode, f'{directory}_WORKSPACE_SIRIUS', 'npc_summary.csv')
                canopus_annotations = pd.read_csv(canopus_npc_path, encoding="utf-8").fillna('Unknown')

                for _, row in canopus_annotations.iterrows():
                   
                    usi = f"mzspec:{metadata['massive_id'][0]}:{metadata.sample_id[0]}_features_ms2_{ionization_mode}.mgf:scan:{row['name']}"
                    feature_id = ns_kg[f'lcms_feature_{usi}']
                    canopus_annotation_id = ns_kg[f"canopus_{usi}"]

                    npc_pathway = ns_kg["npc_" + row['pathway'].translate(greek2latin).replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')]
                    npc_superclass = ns_kg["npc_" + row['superclass'].translate(greek2latin).replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')]
                    npc_class = ns_kg["npc_" + row['class'].translate(greek2latin).replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')]

                    g.add((feature_id, ns_kg.has_canopus_annotation, canopus_annotation_id))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway, npc_pathway))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_pathway_prob, Literal(row['pathwayProbability'], datatype=XSD.float)))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass, npc_superclass))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_superclass_prob, Literal(row['superclassProbability'], datatype=XSD.float)))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class, npc_class))
                    g.add((canopus_annotation_id, ns_kg.has_canopus_npc_class_prob, Literal(row['classProbability'], datatype=XSD.float)))
                    g.add((canopus_annotation_id, RDF.type, ns_kg.SiriusCanopusAnnotation))

            except Exception as e:
                print(f"Error in {directory}: {e}\n{traceback.format_exc()}")
        
        elif sirius_version == 5:
                # Canopus NPC results integration for sirius 5
                try:
                    canopus_npc_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'canopus_compound_summary.tsv')
                    canopus_annotations = pd.read_csv(canopus_npc_path, encoding="utf-8").fillna('Unknown')

                    for _, row in canopus_annotations.iterrows():
                        
                        feature_id_int = row['id'].rsplit('_', 1)[1]
                        usi = f"mzspec:{metadata['massive_id'][0]}:{metadata['sample_id'][0]}_features_ms2_{ionization_mode}.mgf:scan:{int(feature_id_int)}"
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
                except FileNotFoundError:
                    return
                
        elif sirius_version == 6:
                # Canopus NPC results integration for sirius 5
                try:
                    canopus_npc_path = os.path.join(path, directory, ionization_mode, directory + '_WORKSPACE_SIRIUS', 'canopus_structure_summary.tsv')
                    canopus_annotations = pd.read_csv(canopus_npc_path, encoding="utf-8").fillna('Unknown')

                    for _, row in canopus_annotations.iterrows():
                        
                        feature_id_int = row['mappingFeatureId']
                        usi = f"mzspec:{metadata['massive_id'][0]}:{metadata['sample_id'][0]}_features_ms2_{ionization_mode}.mgf:scan:{int(feature_id_int)}"
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
                except FileNotFoundError:
                    return

    except Exception as e:
        print(f"Error processing {directory}: {e}\n{traceback.format_exc()}")

    pathout = os.path.join(sample_dir_path, directory, "rdf/")
    os.makedirs(pathout, exist_ok=True)
    pathout = os.path.normpath(os.path.join(pathout, f'canopus_{ionization_mode}.{output_format}'))
    g.serialize(destination=pathout, format=output_format, encoding="utf-8")

    
def main():
    directories = [d for d in os.listdir(sample_dir_path) if os.path.isdir(os.path.join(sample_dir_path, d))]
    
    with ProcessPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(process_directory, d): d for d in directories}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {futures[future]}: {e}")

if __name__ == "__main__":
    main()