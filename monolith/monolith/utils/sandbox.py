"""Notebook to assemble LOTUS and newer metadata"""

import os
from pathlib import Path


os.chdir(os.getcwd())

p = Path(__file__).parents[2]
os.chdir(p)


import pandas as pd
from typing import List
from monolith.utils import get_classification_results
from monolith.utils import unique_inchikey


path_to_lotus = "./downloads/taxo_db_metadata.csv"

# Load the metadata table

metadata_lotus = pd.read_csv(path_to_lotus)

metadata = metadata_lotus

# We print some information about the table

print(metadata.info())


# First thing. We drop all chemical taxonomies. These columns are prefixed by 'structure_taxonomy_'

metadata = metadata.loc[:, ~metadata.columns.str.startswith("structure_taxonomy_")]

# We now drop any duplicated rows

metadata = metadata.drop_duplicates()


# We make sure that we have not lost IK in the process

unique_inchikey(metadata).shape[0] == unique_inchikey(metadata_lotus).shape[0]


# We now fetch the classification results form the DuckDB

classification_results = get_classification_results("./npc_classification.duckdb")

# We get print some information about the classification results

print(classification_results.info())

# The classification is saved as a tsv file.

classification_results.to_csv("./downloads/classification_results.tsv", sep="\t", index=False)