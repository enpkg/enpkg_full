"""Scripts to get some metrics on the LOTUS metadata table."""

import pandas as pd
from typing import List


path_to_lotus = "monolith/downloads/taxo_db_metadata.csv"

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
metadata_unique_multi_pw = inchikey_with_multiple_pathways(metadata_unique)


# Function to fetch the NPC classification for a given SMILES. We use the following https://npclassifier.gnps2.org/classify?smiles=CC(C)C(N)C(=O)NOC(CC(=O)O)C(=O)O

import requests


def get_npc_classification(smiles):
    url = f"https://npclassifier.gnps2.org/classify?smiles={smiles}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code



get_npc_classification("Nc1ncnc2c1ncn2C1OC(COP(=O)(O)OP(=O)(O)OCC2OC([n+]3cccc(C(=O)O)c3)C(O)C2O)C(O)C1O")


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


# Function to get NPC classification
def get_npc_classification(smiles):
    url = f"https://npclassifier.gnps2.org/classify?smiles={smiles}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

get_npc_classification("C=CC(C)(C)n1cc(CC(NC)C(=O)O)c2ccccc21")


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
