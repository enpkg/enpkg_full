"""Notebook to assemble LOTUS and newer metadata"""


from pathlib import Path


os.chdir(os.getcwd())

p = Path(__file__).parents[2]
os.chdir(p)


import pandas as pd
from typing import List
from monolith.utils import get_classification_results


path_to_lotus = "./downloads/taxo_db_metadata.csv"

# Load the metadata table

metadata = pd.read_csv(path_to_lotus)


# 