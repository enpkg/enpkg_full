import pandas as pd
import os
from matchms.importing import load_from_mgf
from matchms.exporting import save_as_mgf
from tqdm import tqdm
import argparse
import textwrap
from pathlib import Path

p = Path(__file__).parents[2]
os.chdir(p)

""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent(
        """\
        This script generate an aggregated .mgf spectra file from unaligned individual .mgf files for further GNPS classical MN processing. 
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
            - ionization mode of spectra to aggregate
            - Output name for the output
        """
    ),
)
parser.add_argument(
    "-p",
    "--sample_dir_path",
    required=True,
    help="The path to the directory where samples folders to process are located",
)
parser.add_argument(
    "-ion", "--ionization", required=True, help="The ionization mode to aggregate"
)
parser.add_argument(
    "-out",
    "--output_name",
    required=True,
    help="The the output name for the .mgf and the .csv file to generate",
)

args = parser.parse_args()
sample_dir_path = args.sample_dir_path
ionization = args.ionization
output_name = args.output_name

""" Process """

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]
spectrums = []
i = 1
j = 1

n_iter = len(samples_dir)
treated_samples = []
for sample_directory in tqdm(samples_dir):
    if ionization == "pos":
        mgf_file_path = os.path.join(
            path,
            sample_directory,
            ionization,
            sample_directory + "_features_ms2_pos.mgf",
        )
    elif ionization == "neg":
        mgf_file_path = os.path.join(
            path,
            sample_directory,
            ionization,
            sample_directory + "_features_ms2_neg.mgf",
        )
    else:
        raise ValueError("ionization must be pos or neg")
    metadata_file_path = os.path.join(
        path, sample_directory, sample_directory + "_metadata.tsv"
    )
    try:
        sample_spec = list(load_from_mgf(mgf_file_path))
        metadata = pd.read_csv(metadata_file_path, sep="\t")
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    if metadata["sample_type"][0] == "sample":
        treated_samples.append(sample_directory)
        for spectrum in sample_spec:
            usi = (
                "mzspec:"
                + metadata["massive_id"][0]
                + ":"
                + metadata.sample_id[0]
                + "_features_ms2_"
                + ionization
                + ".mgf:scan:"
                + str(spectrum.metadata["scans"])
            )
            original_feat_id = "lcms_feature_" + usi
            # original_feat_id = sample_directory + '_feature_' + spectrum.metadata['scans'] + '_' + ionization
            spectrum.set("original_feature_id", original_feat_id)
            spectrum.set("feature_id", i)
            spectrum.set("scans", i)
            i += 1
        spectrums = spectrums + sample_spec

metadata_df = pd.DataFrame(s.metadata for s in spectrums)

os.makedirs(path + "/001_aggregated_spectra/", exist_ok=True)
metadata_df.to_csv(
    path + "/001_aggregated_spectra/" + output_name + "_metadata.csv", index=False
)

spec_path = os.path.normpath(path + "/001_aggregated_spectra/" + output_name + ".mgf")
param_path = os.path.normpath(
    path + "/001_aggregated_spectra/" + output_name + "_params.csv"
)
if os.path.isfile(spec_path):
    os.remove(spec_path)
    save_as_mgf(spectrums, spec_path)
else:
    save_as_mgf(spectrums, spec_path)
pd.DataFrame(treated_samples, columns=["treated_samples"]).to_csv(
    param_path, index=False
)
