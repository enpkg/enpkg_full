"""Scripts to get some metrics on the LOTUS metadata table."""

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

# Function to keep only unique inchikeys, npclassifier_01pathway combinations and return the full dataframe.


def unique_inchikey_pathway(metadata):
    metadata_unique = metadata.drop_duplicates(
        subset=["structure_inchikey", "structure_taxonomy_npclassifier_01pathway"]
    )
    print(f"Number of unique inchikey-pathway combinations: {metadata_unique.shape[0]}")

    return metadata_unique


def unique_inchikey(metadata):
    metadata_unique = metadata.drop_duplicates(subset=["structure_inchikey"])
    print(f"Number of unique inchikey: {metadata_unique.shape[0]}")

    return metadata_unique


metadata_unique_ik_pw = unique_inchikey_pathway(metadata)
metadata_unique_ik = unique_inchikey(metadata)


def count_inchikey_with_multiple_pathways(df):
    # Group by structure_inchikey and count unique npc_pathways for each inchikey
    pathway_counts = df.groupby("structure_inchikey")[
        "structure_taxonomy_npclassifier_01pathway"
    ].nunique()

    # Filter inchikeys that have two or more pathways
    inchikey_multiple_pathways = pathway_counts[pathway_counts >= 2].count()

    return inchikey_multiple_pathways


# Same function but return the inchikeys with multiple pathways. Display also the multiple pathways.


def inchikey_with_multiple_pathways(df):
    # Group by structure_inchikey and count unique npc_pathways for each inchikey
    pathway_counts = df.groupby("structure_inchikey")[
        "structure_taxonomy_npclassifier_01pathway"
    ].nunique()

    # Filter inchikeys that have two or more pathways
    inchikey_multiple_pathways = pathway_counts[pathway_counts >= 2]

    return inchikey_multiple_pathways


# Same function but return the inchikeys with multiple pathways. Display also the multiple pathways. And the SMILES.


def inchikey_with_multiple_pathways(df):
    # Group by structure_inchikey and count unique npc_pathways for each inchikey
    pathway_counts = df.groupby("structure_inchikey")[
        "structure_taxonomy_npclassifier_01pathway"
    ].nunique()

    # Filter inchikeys that have two or more pathways
    inchikey_multiple_pathways = pathway_counts[pathway_counts >= 2]

    inchikey_multiple_pathways = inchikey_multiple_pathways.reset_index()

    inchikey_multiple_pathways = inchikey_multiple_pathways.merge(
        df[
            [
                "structure_inchikey",
                "structure_smiles",
                "structure_taxonomy_npclassifier_01pathway",
            ]
        ],
        on="structure_inchikey",
        how="left",
    )

    return inchikey_multiple_pathways


count_inchikey_with_multiple_pathways(metadata_unique)
metadata_unique_multi_pw = inchikey_with_multiple_pathways(metadata_unique_ik_pw)


# Function to fetch the NPC classification for a given SMILES. We use the following https://npclassifier.gnps2.org/classify?smiles=CC(C)C(N)C(=O)NOC(CC(=O)O)C(=O)O

import requests


def get_npc_classification(smiles):
    url = f"https://npclassifier.gnps2.org/classify?smiles={smiles}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


get_npc_classification(
    "Nc1ncnc2c1ncn2C1OC(COP(=O)(O)OP(=O)(O)OCC2OC([n+]3cccc(C(=O)O)c3)C(O)C2O)C(O)C1O"
)


# Return NPC classification from the LOTUS metadata table for a given SMILES


def get_npc_classification_from_metadata(metadata, smiles):
    npc_classification = metadata[metadata["structure_smiles"] == smiles][
        "structure_taxonomy_npclassifier_01pathway"
    ]

    return npc_classification


get_npc_classification_from_metadata(
    metadata_unique, "C=CC(C)(C)n1cc(CC(NC)C(=O)O)c2ccccc21"
)


import pandas as pd
import requests
from tqdm import tqdm
from urllib.parse import quote

# Function to get NPC classification
def get_npc_classification(smiles):
    # Encode the SMILES string
    encoded_smiles = quote(smiles)

    print(f"Fetching data for encode SMILES: {encoded_smiles}")

    url = f"https://npclassifier.gnps2.org/classify?smiles={encoded_smiles}"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for SMILES: {smiles} - Status Code: {response.status_code}")
        return None

get_npc_classification("C=CC(C)(C)n1cc(CC(NC)C(=O)O)c2ccccc21")
get_npc_classification("CCCCCCCCCCCCC/C=C/[C@@H](O)[C@@H](N)COP(=O)(O)OCC[N+](C)(C)C")
get_npc_classification("COc1ccc2c(c1O)-c1c(O)c(OC)cc3c1C(C2)[N+](C)(C)CC3")


COc1ccc2c(c1O)-c1c(O)c(OC)cc3c1C(C2)[N+](C)(C)CC3

COc1ccc2c%28c1O%29-c1c%28O%29c%28OC%29cc3c1C%28C2%29%5BN%2B%5D%28C%29%28C%29CC3
COc1ccc2c%COc1ccc2c(c1O)-c1c(O)c(OC)cc3c1C(C2)%5BN%2B%5D(C)(C)CC3


# Function to classify and add NPC levels to the DataFrame
def add_npc_classification(df, smiles_column="structure_smiles"):
    # Initialize new columns
    df["npc_pathway"] = None
    df["npc_superclass"] = None
    df["npc_class"] = None

    # Iterate over each row and classify each SMILES
    for index, row in tqdm(df.iterrows(), total=len(df)):
        smiles = row[smiles_column]
        npc_result = get_npc_classification(smiles)

        if npc_result:
            # Combine all results into a comma-separated string, if available
            df.at[index, "npc_pathway"] = (
                ", ".join(npc_result["pathway_results"])
                if npc_result["pathway_results"]
                else None
            )
            df.at[index, "npc_superclass"] = (
                ", ".join(npc_result["superclass_results"])
                if npc_result["superclass_results"]
                else None
            )
            df.at[index, "npc_class"] = (
                ", ".join(npc_result["class_results"])
                if npc_result["class_results"]
                else None
            )

    return df


# Load your dataset into a DataFrame
# df = pd.read_csv("your_file.csv")  # Uncomment and replace "your_file.csv" with your actual file path

# Example usage:
df_npc = add_npc_classification(metadata_unique_multi_pw[:20], "structure_smiles")
print(df_npc.head())




# Example usage:
df_classifications = get_classification_results(db_name="./npc_classification.duckdb")
print(df_classifications.head())


# We list the IK which have not been classified by making the difference between the LOTUS input set and the classified set.

input_set = set(metadata_unique_ik["structure_inchikey"])
classified_set = set(df_classifications["inchikey"])

unclassified_set = input_set - classified_set

print(f"Number of unclassified InChIKeys: {len(unclassified_set)}")

# We now subset the metadata table to only keep the unclassified InChIKeys

metadata_unclassified = metadata_unique_ik[
    metadata_unique_ik["structure_inchikey"].isin(unclassified_set)
]

# We save this subset to a CSV file

metadata_unclassified.to_csv("downloads/unclassified_inchikeys.csv", index=False)

