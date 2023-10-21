import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from tqdm import tqdm
from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz, add_losses, normalize_intensities, reduce_to_number_of_peaks
from pathlib import Path
from spec2vec import SpectrumDocument
import yaml
import git
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

p = Path(__file__).parents[2]
os.chdir(p)

# Loading the parameters from yaml file


if not os.path.exists('config/params.yaml'):
    print('No config/params.yaml: copy from config/template.yaml and modify according to your needs')
with open(r'config/params.yaml') as file:
    params_list = yaml.load(file, Loader=yaml.FullLoader)

sample_dir_path = os.path.normpath(params_list['sample_dir_path'])
ionization_mode = params_list['ionization_mode']
output_format = params_list['graph_format']


kg_uri = params_list['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list['prefix']

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

def process_directory(directory):
    # Skip hidden directories or specific files like .DS_store
    if directory.startswith('.'):
        return None

    try:
        # Construct the paths based on the directory input.
        mgf_path = os.path.join(path, directory, ionization_mode, directory + '_features_ms2_' + ionization_mode + '.mgf')
        metadata_path = os.path.join(path, directory, directory + '_metadata.tsv')
        
        # Check if the required files are accessible.
        if not os.path.isfile(mgf_path) or not os.path.isfile(metadata_path):
            print(f"Required files for {directory} are missing.")
            return None

        # Read the metadata file.
        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] == 'sample':
            g = Graph()
            nm = g.namespace_manager
            nm.bind(prefix, ns_kg)

            # Load and filter spectra from mgf file
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
            
            # Create the output directory if it doesn't exist.
            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.normpath(os.path.join(pathout, f'features_spec2vec_{ionization_mode}.{output_format}'))
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            
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
            
            # Instead of printing, return the result message.
            return f'Results are in : {pathout}'

        else:
            print(f"Sample type for {directory} is not 'sample'.")
            return None

    except Exception as e:
        print(f"An error occurred while processing {directory}: {str(e)}")
        # Optionally, log the traceback here if you need more information about exceptions.
        # This will not halt the execution of other tasks.
        return None

def main():

    # Define the maximum number of workers (threads or processes).
    max_workers = 32  # Or another number suitable for your system's capabilities

    path = os.path.normpath(sample_dir_path)
    samples_dir = [directory for directory in os.listdir(path)]


    # Creating a lock object to control access to the progress bar update function
    lock = threading.Lock()

    # Creating a progress bar object with tqdm (this object is not fully thread-safe)
    progress_bar = tqdm(total=len(samples_dir), position=0, leave=True)

    # Function to safely update the progress bar by one step
    def safe_update():
        with lock:
            progress_bar.update(1)

    # Using ThreadPoolExecutor to process the directories in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Dictionary to hold the future objects
        future_to_directory = {executor.submit(process_directory, directory): directory for directory in samples_dir}

        for future in as_completed(future_to_directory):
            directory = future_to_directory[future]
            try:
                # The result from the future object
                result = future.result()
                if result:
                    print(f"Directory {directory} processed: {result}")
                else:
                    print(f"Directory {directory} had no output (possibly skipped).")
            except Exception as exc:
                print(f"Directory {directory} generated an exception: {exc}")
            finally:
                # Safely update the progress bar, accounting for possible race conditions
                safe_update()

    # Ensuring the progress bar visually reflects completion before exiting
    progress_bar.close()

# Entry point of your script
if __name__ == "__main__":
    main()
