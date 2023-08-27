import os
import argparse
import textwrap
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from tqdm import tqdm
from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz
from matchms.filtering import add_losses
from matchms.filtering import normalize_intensities
from matchms.filtering import reduce_to_number_of_peaks
from pathlib import Path
from spec2vec import SpectrumDocument
import yaml
import git

p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script generate a RDF graph (.ttl format) from the features' MS/MS spectra using spec2vec
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
            - Ionization mode to process
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')
parser.add_argument('-ion', '--ionization_mode', required=True,
                    help='The ionization mode to process')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
ionization_mode = args.ionization_mode

# Define function
def load_and_filter_from_mgf(path) -> list:
    """Load and filter spectra from mgf file
    Returns:
        spectrums (list of matchms.spectrum): a list of matchms.spectrum objects
    """
    def apply_filters(spectrum):
        spectrum = add_precursor_mz(spectrum)
        spectrum = normalize_intensities(spectrum)
        spectrum = reduce_to_number_of_peaks(spectrum, n_required=1, n_max=100)
        spectrum = add_precursor_mz(spectrum)
        spectrum = add_losses(spectrum, loss_mz_from=10, loss_mz_to=250)
        return spectrum

    spectra_list = [apply_filters(s) for s in load_from_mgf(path)]
    spectra_list = [s for s in spectra_list if s is not None]
    return spectra_list 

path = os.path.normpath(sample_dir_path)

kg_uri = "https://enpkg.commons-lab.org/kg/"
ns_kg = rdflib.Namespace(kg_uri)
prefix = "enpkg"

i=1
samples_dir = [directory for directory in os.listdir(path)]
for directory in tqdm(samples_dir):

    #ignoring .DS_store and hidden folders
    if not directory.startswith('.') :
        
        mgf_path = os.path.join(path, directory, ionization_mode, directory + '_features_ms2_' + ionization_mode + '.mgf')
        metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
        try:
            metadata = pd.read_csv(metadata_path, sep='\t')
            os.path.isfile(mgf_path)
        except FileNotFoundError:
            continue
        except NotADirectoryError:
            continue

        if metadata.sample_type[0] == 'sample':
            g = Graph()
            nm = g.namespace_manager
            nm.bind(prefix, ns_kg)

            spectra_list = load_and_filter_from_mgf(mgf_path)
            reference_documents = [SpectrumDocument(s, n_decimals=2) for s in spectra_list]
            list_peaks_losses = list(doc.words for doc in reference_documents)
            sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])
            for spectrum, document in zip(spectra_list, list_peaks_losses):
                usi = 'mzspec:' + metadata['massive_id'][0] + ':' + metadata.sample_id[0] + '_features_ms2_'+ ionization_mode+ '.mgf:scan:' + str(int(spectrum.metadata['feature_id']))
                feature_id = rdflib.term.URIRef(kg_uri + 'lcms_feature_' + usi)
                document_id = rdflib.term.URIRef(kg_uri + 'spec2vec_doc_' + usi)
                
                # Add peak intensities as feature attributes
                g.add((feature_id, ns_kg.has_raw_spectrum, rdflib.term.Literal(tuple(zip(spectrum.mz, spectrum.intensities)))))
                
                g.add((feature_id, ns_kg.has_spec2vec_doc, document_id))
                g.add((document_id, RDF.type, ns_kg.Spec2VecDoc))
                g.add((document_id, RDFS.label, rdflib.term.Literal(f"Spec2vec document of feature {str(int(spectrum.metadata['feature_id']))} from sample {metadata.sample_id[0]} in {ionization_mode} mode")))
                for word in document:
                    word = word.replace('@', '_')
                    if word.startswith('peak'):
                        peak = rdflib.term.URIRef(kg_uri + word)
                        g.add((document_id, ns_kg.has_spec2vec_peak, peak))
                        g.add((peak, ns_kg.has_value, rdflib.term.Literal(word.split('_')[1], datatype=XSD.float)))
                        g.add((peak, RDFS.label, rdflib.term.Literal(f"Spec2vec peak of value {word.split('_')[1]}")))
                        g.add((peak, RDF.type, ns_kg.Spec2VecPeak))
                    elif word.startswith('loss'):
                        loss = rdflib.term.URIRef(kg_uri + word)
                        g.add((document_id, ns_kg.has_spec2vec_loss, loss))
                        g.add((loss, ns_kg.has_value, rdflib.term.Literal(word.split('_')[1], datatype=XSD.float)))
                        g.add((loss, RDFS.label, rdflib.term.Literal(f"Spec2vec loss of value {word.split('_')[1]}")))
                        g.add((loss, RDF.type, ns_kg.Spec2VecLoss))

            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(os.path.join(pathout, f'features_spec2vec_{ionization_mode}.ttl'))
            g.serialize(destination=pathout, format="ttl", encoding="utf-8")
            
            # Save parameters:
            params_path = os.path.join(sample_dir_path, directory, "rdf", "graph_params.yaml")
            
            if os.path.isfile(params_path):
                with open(params_path, encoding='UTF-8') as file:    
                    params_list = yaml.load(file, Loader=yaml.FullLoader) 
            else:
                params_list = {}  
                    
            params_list.update({f'features_spec2vec_{ionization_mode}':[{'git_commit':git.Repo(search_parent_directories=True).head.object.hexsha},
                                {'git_commit_link':f'https://github.com/enpkg/enpkg_graph_builder/tree/{git.Repo(search_parent_directories=True).head.object.hexsha}'}]})
            
            with open(os.path.join(params_path), 'w', encoding='UTF-8') as file:
                yaml.dump(params_list, file)
                
            print(f'Results are in : {pathout}')
            