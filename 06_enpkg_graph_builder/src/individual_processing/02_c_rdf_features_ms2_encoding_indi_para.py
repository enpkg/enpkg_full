from concurrent.futures import ProcessPoolExecutor
import traceback
import os
import pandas as pd
import rdflib
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, XSD
from tqdm import tqdm
from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz, reduce_to_number_of_peaks, add_losses, remove_peaks_around_precursor_mz
from pathlib import Path
import yaml
import git
import sys
from pathlib import Path

# Function to substitute variables in YAML
def substitute_variables(config):
    """Recursively substitute variables in the YAML configuration."""
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

    # Context for substitution
    context = {
        "general.root_data_path": config["general"]["root_data_path"],
        "general.treated_data_path": config["general"]["treated_data_path"],
        "general.polarity": config["general"]["polarity"],
    }
    recurse_dict(config, context)
    return config


# Loading and substituting YAML parameters
p = Path(__file__).parents[2]
os.chdir(p)

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    sys.exit(1)

with open('../params/user.yml') as file:
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list_full = substitute_variables(params_list_full)

# Extract parameters
sample_dir_path = os.path.normpath(params_list_full['general']['treated_data_path'])
ionization_mode = params_list_full['general']['polarity']
output_format = params_list_full['graph-builder']['graph_format']
kg_uri = params_list_full['graph-builder']['kg_uri']
ns_kg = rdflib.Namespace(kg_uri)
prefix = params_list_full['graph-builder']['prefix']
n_decimals = params_list_full['graph-builder']['peak_loss_params']['n_decimals']

print(f"Resolved sample_dir_path: {sample_dir_path}")
if not os.path.exists(sample_dir_path):
    print(f"Sample directory path not found: {sample_dir_path}")
    sys.exit(1)

<<<<<<< Updated upstream
# Define spectra filtering functions
def load_and_filter_from_mgf(path) -> list:
    """Load and filter spectra from MGF file."""
    def apply_filters(spectrum):
        spectrum = add_precursor_mz(spectrum) #add precursor m/z if missing
        spectrum = remove_peaks_around_precursor_mz(spectrum, mz_tolerance=17.0) # Remove peaks that are within mz_tolerance (in Da) of the precursor mz, exlcuding the precursor peak.
        spectrum = reduce_to_number_of_peaks(spectrum, n_required=1, n_max=100) #max number of peaks per spectrum to keep
        spectrum = add_losses(spectrum, loss_mz_from=10, loss_mz_to=600) #add neutral losses to the spectrum up to a 600 Da loss
=======
def load_and_filter_from_mgf(path) -> list:
    """Load and filter spectra from MGF file."""
    def apply_filters(spectrum):
        spectrum = add_precursor_mz(spectrum)
        spectrum = reduce_to_number_of_peaks(spectrum, n_required=1, n_max=100)
        spectrum = remove_peaks_around_precursor_mz(spectrum, mz_tolerance=17.0) # Remove peaks that are within mz_tolerance (in Da) of the precursor mz, exlcuding the precursor peak.
        spectrum = add_losses(spectrum, loss_mz_from=10, loss_mz_to=250)
>>>>>>> Stashed changes
        return spectrum

    spectra_list = [apply_filters(s) for s in load_from_mgf(path)]
    return [s for s in spectra_list if s is not None]

<<<<<<< Updated upstream
# Process each directory
def process_directory(directory):
=======
def process_directory(directory):
    """Process a directory and encode spectra as ms2_list."""
>>>>>>> Stashed changes
    mgf_path = os.path.join(sample_dir_path, directory, ionization_mode, f"{directory}_features_ms2_{ionization_mode}.mgf")
    metadata_path = os.path.join(sample_dir_path, directory, f"{directory}_metadata.tsv")

    try:
        if not os.path.isfile(metadata_path) or not os.path.isfile(mgf_path):
            print(f"Skipping {directory}, missing files.")
            return f"Skipped {directory} due to missing files."

        metadata = pd.read_csv(metadata_path, sep='\t')

        if metadata.sample_type[0] == 'sample':
            g = Graph()
            g.namespace_manager.bind(prefix, ns_kg)

            spectra_list = load_and_filter_from_mgf(mgf_path)
<<<<<<< Updated upstream
            #reference_documents = [SpectrumDocument(s, n_decimals=n_decimals) for s in spectra_list]
            #list_peaks_losses = list(doc.words for doc in reference_documents)
            sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])

            for spectrum, document in zip(spectra_list, list_peaks_losses):
                usi = f"mzspec:{metadata['massive_id'][0]}:{metadata['sample_id'][0]}_features_ms2_{ionization_mode}.mgf:scan:{int(spectrum.metadata['feature_id'])}"
                feature_id = rdflib.term.URIRef(f"{kg_uri}lcms_feature_{usi}")
                document_id = rdflib.term.URIRef(f"{kg_uri}spec2vec_doc_{usi}")

                # Add peak intensities as feature attributes
                g.add((feature_id, ns_kg.has_raw_spectrum, rdflib.term.Literal(tuple(zip(spectrum.mz, spectrum.intensities)))))
                g.add((feature_id, ns_kg.has_spec2vec_doc, document_id))
                g.add((document_id, RDF.type, ns_kg.Spec2VecDoc))
                g.add((document_id, RDFS.label, rdflib.term.Literal(f"Spec2vec document of feature {spectrum.metadata['feature_id']} from sample {metadata.sample_id[0]} in {ionization_mode} mode")))

                for word in document:
                    word = word.replace('@', '_')
                    if word.startswith('peak'):
                        peak = rdflib.term.URIRef(f"{kg_uri}{word}")
                        g.add((document_id, ns_kg.has_spec2vec_peak, peak))
                        g.add((peak, ns_kg.has_value, rdflib.term.Literal(word.split('_')[1], datatype=XSD.float)))
                        g.add((peak, RDFS.label, rdflib.term.Literal(f"Spec2vec peak of value {word.split('_')[1]}")))
                        g.add((peak, RDF.type, ns_kg.Spec2VecPeak))
                    elif word.startswith('loss'):
                        loss = rdflib.term.URIRef(f"{kg_uri}{word}")
                        g.add((document_id, ns_kg.has_spec2vec_loss, loss))
                        g.add((loss, ns_kg.has_value, rdflib.term.Literal(word.split('_')[1], datatype=XSD.float)))
                        g.add((loss, RDFS.label, rdflib.term.Literal(f"Spec2vec loss of value {word.split('_')[1]}")))
                        g.add((loss, RDF.type, ns_kg.Spec2VecLoss))

            # Save the graph
            pathout = os.path.join(sample_dir_path, directory, "rdf/")
            os.makedirs(pathout, exist_ok=True)
            pathout = os.path.join(pathout, f"features_spec2vec_{ionization_mode}.{output_format}")
            g.serialize(destination=pathout, format=output_format, encoding="utf-8")
            print(f"Results are in: {pathout}")
            return f"Processed {directory}"

    except Exception as e:
        error_message = f"Error processing {directory}: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return error_message
=======
            reference_ms2_lists = spectra_list  # Use spectra directly

            sample = rdflib.term.URIRef(kg_uri + metadata.sample_id[0])

            for spectrum in reference_ms2_lists:
                usi = f"mzspec:{metadata['massive_id'][0]}:{metadata['sample_id'][0]}_features_ms2_{ionization_mode}.mgf:scan:{int(spectrum.metadata['feature_id'])}"
                feature_id = rdflib.term.URIRef(f"{kg_uri}lcms_feature_{usi}")
                ms2_list_id = rdflib.term.URIRef(f"{kg_uri}ms2_list_{usi}")

                # Create ms2_list_text as a formatted string
                ms2_list_text = "\n".join(f"{mz:.4f} {intensity:.4e}" for mz, intensity in zip(spectrum.peaks.mz, spectrum.peaks.intensities))

                # Store ms2_list_text in the RDF graph
                g.add((feature_id, ns_kg.has_raw_spectrum, rdflib.term.Literal(ms2_list_text)))
                g.add((feature_id, ns_kg.has_ms2_list, ms2_list_id))
                g.add((ms2_list_id, RDF.type, ns_kg.MS2List))
                g.add((ms2_list_id, RDFS.label, rdflib.term.Literal(f"MS2 list of feature {spectrum.metadata['feature_id']} from sample {metadata.sample_id[0]} in {ionization_mode} mode")))

                # Encode peaks
                for mz, intensity in zip(spectrum.peaks.mz, spectrum.peaks.intensities):
                    peak = rdflib.term.URIRef(f"{kg_uri}peak_{mz:.4f}")
                    g.add((ms2_list_id, ns_kg.has_peak, peak))
                    g.add((peak, ns_kg.has_mz, rdflib.term.Literal(mz, datatype=XSD.float)))
                    g.add((peak, ns_kg.has_intensity, rdflib.term.Literal(intensity, datatype=XSD.float)))
                    g.add((peak, RDF.type, ns_kg.Peak))
                    g.add((peak, RDFS.label, rdflib.term.Literal(f"MS2 peak with m/z {mz:.4f} and intensity {intensity:.4f}")))

                # Encode losses if present
                if spectrum.losses:
                    for loss_mz, loss_intensity in zip(spectrum.losses.mz, spectrum.losses.intensities):
                        loss = rdflib.term.URIRef(f"{kg_uri}loss_{loss_mz:.4f}")
                        g.add((ms2_list_id, ns_kg.has_loss, loss))
                        g.add((loss, ns_kg.has_mz, rdflib.term.Literal(loss_mz, datatype=XSD.float)))
                        g.add((loss, ns_kg.has_intensity, rdflib.term.Literal(loss_intensity, datatype=XSD.float)))
                        g.add((loss, RDF.type, ns_kg.Loss))
                        g.add((loss, RDFS.label, rdflib.term.Literal(f"Loss with m/z {loss_mz:.4f} and intensity {loss_intensity:.4f}")))

                        # Save the graph
                        pathout = os.path.join(sample_dir_path, directory, "rdf/")
                        os.makedirs(pathout, exist_ok=True)
                        pathout = os.path.join(pathout, f"features_ms2_list_{ionization_mode}.{output_format}")
                        g.serialize(destination=pathout, format=output_format, encoding="utf-8")
                        print(f"Results are in: {pathout}")
                        return f"Processed {directory}"

    except Exception as e:
        print(f"Error processing {directory}: {e}")
        return f"Error processing {directory}: {e}"
>>>>>>> Stashed changes

# Main function
def main():
    samples_dir = [directory for directory in os.listdir(sample_dir_path) if not directory.startswith('.')]
    with ProcessPoolExecutor(max_workers=32) as executor:
        results = executor.map(process_directory, samples_dir)

    for result in results:
        print(result)

if __name__ == "__main__":
    main()
