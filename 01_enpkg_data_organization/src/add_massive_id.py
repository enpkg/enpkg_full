"""Argument parser """
import argparse
import os
import re
import textwrap

import pandas as pd

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent(
        """\
        Add the MassIVE id of the repository where .mz(X)ML and features_ms2_pos/neg_.mgf data have been uploaded to the metadata file.
        """
    ),
)

parser.add_argument(
    "--massive_id",
    required=True,
    help="The MassIVE id (format MSVXXXXXXXXX, ex. MSV000087728) of the repository where .mz(X)ML \
                        and features_ms2_pos/neg_.mgf data have been uploaded",
)
parser.add_argument(
    "-p",
    "--sample_dir_path",
    required=True,
    help="The path to the directory where \
                    samples folders corresponding to the MassIVE id are located",
)

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
massive_id = os.path.normpath(args.massive_id)

# Check if format of MassIVE ID is correct:
if not bool(re.match("MSV\d\d\d\d\d\d\d\d\d$", massive_id)):
    raise ValueError("Invalid MassIVE ID, must be in format MSVXXXXXXXXX")

path = os.path.normpath(sample_dir_path)
samples_dir = [directory for directory in os.listdir(path)]

for sample_directory in samples_dir:
    metadata_file_path = os.path.join(
        path, sample_directory, sample_directory + "_metadata.tsv"
    )
    try:
        metadata = pd.read_csv(metadata_file_path, sep="\t")
    except FileNotFoundError:
        continue
    except NotADirectoryError:
        continue
    metadata["massive_id"] = massive_id
    metadata.to_csv(metadata_file_path, sep="\t", index=False)
