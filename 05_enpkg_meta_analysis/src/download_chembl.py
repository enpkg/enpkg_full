import pandas as pd
import argparse
import textwrap
from chembl_webresource_client.new_client import new_client
from rdkit.Chem import AllChem
import os
from pandas import json_normalize
import requests
from json import JSONDecodeError
from rdkit.Chem import RDConfig
import os
import sys

sys.path.append(os.path.join(RDConfig.RDContribDir, "NP_Score"))
import npscorer


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent(
        """\
         This script will download compounds from ChEMBL DB with an activity against a given target
         --------------------------------
            You should just enter the ChEMBL target ID
            results will be stored in ../output_data/chembl/<target_id>_np_like_min_<NPlike_score>.csv
        """
    ),
)
parser.add_argument(
    "-id",
    "--target_id",
    required=True,
    help="The ChEMBL target ID to use to select compounds",
)
parser.add_argument(
    "-npl",
    "--NPlike_score",
    default=-1,
    help='The minimal NP likeliness score for compounds. Compounds with \
                        lower NP likeliness score (i.e. "less natural") will be filterd out. Default -1.',
)
args = parser.parse_args()

""" Functions """


# Function used to clean the data downloaded from ChEMBL
def clean_DB(df_in, NP_model, NP_cutoff):
    """Function to clean a ChEMBL DB"""

    df = df_in.copy()
    isomeric_smiles = []
    np_scores = []
    inchikey = []

    # Drop rows without Smiles or activity value
    df.dropna(subset=["canonical_smiles", "standard_value"], inplace=True)

    # Drop row with a Data Validity Comment "Outside typical range"
    df.drop(
        df[df["data_validity_comment"] == "Outside typical range"].index, inplace=True
    )
    df.drop(
        [
            "data_validity_comment",
            "relation",
            "units",
            "value",
            "activity_comment",
            "type",
        ],
        axis=1,
        inplace=True,
    )

    # Drop rows with an invalid smiles, replace smiles with canonical smiles and add a columns with smiles without stereo-isomers
    mols = []

    for i, row in df.iterrows():
        mol = AllChem.MolFromSmiles(row["canonical_smiles"])
        if mol is not None:
            iso_smiles = AllChem.MolToSmiles(mol, isomericSmiles=True)
            isomeric_smiles.append(iso_smiles)
            inchikey.append(AllChem.MolToInchiKey(mol))
            np_scores.append(npscorer.scoreMol(mol, NP_model))
            row["canonical_smiles"] = AllChem.MolToSmiles(mol)
        else:
            df.drop(i, inplace=True)

    # l=[i for i in range(len(mols)) if mols[i] == None]
    # df.drop(df.index[l], inplace=True)

    # for _, row in df.iterrows():
    #     mol = AllChem.MolFromSmiles(row["canonical_smiles"])
    #     iso_smiles = AllChem.MolToSmiles(mol, isomericSmiles=True)
    #     isomeric_smiles.append(iso_smiles)
    #     inchikey.append(AllChem.MolToInchiKey(mol))

    df["isomeric_smiles"] = isomeric_smiles
    df["inchikey"] = inchikey
    df["np_score"] = np_scores
    df["short_inchikey"] = df["inchikey"].str[:14]
    df["document_journal"].replace({None: "Unknown journal"}, inplace=True)
    df = df[(df["np_score"] > NP_cutoff) | (df["document_journal"] == "J Nat Prod")]

    return df


def get_all_ik(url):
    query = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?ik ?wd ?isomeric_smiles
WHERE{
    ?wd wdt:P235 ?ik .
    optional { ?wd wdt:P2017 ?isomeric_smiles } 
}
  """
    r = requests.get(url, params={"format": "json", "query": query})
    try:
        data = r.json()
        results = pd.DataFrame.from_dict(data).results.bindings
        df = json_normalize(results)
        df.rename(
            columns={
                "wd.value": "wikidata_id",
                "ik.value": "inchikey",
                "isomeric_smiles.value": "isomeric_smiles",
            },
            inplace=True,
        )
        return df[["wikidata_id", "inchikey", "isomeric_smiles"]]
    except JSONDecodeError:
        return None


# Load variables
from pathlib import Path

p = Path(__file__).parents[1]
os.chdir(p)
sql_folder_path = os.path.join(os.getcwd() + "/output_data/chembl/")
Path(sql_folder_path).mkdir(parents=True, exist_ok=True)

# Download selected activities
activities = new_client.activity
activities = activities.filter(target_chembl_id=args.target_id)

res = activities.filter(
    standard_value__isnull=False
)  # Keep only compounds with an activity value
NP_model = npscorer.readNPModel()

# res = activities.filter(standard_type__iexact = 'IC50')
res = res.only(
    [
        "activity_comment",
        "molecule_chembl_id",
        "canonical_smiles",
        "standard_relation",
        "target_chembl_id",
        "standard_type",
        "target_pref_name",
        "standard_units",
        "standard_value",
        "data_validity_comment",
        "document_journal",
        "assay_chembl_id",
        "document_chembl_id",
    ]
)

print("Fetching results from ChEMBL: this step can be long. Have a coffee ;)")
res_df = pd.DataFrame.from_dict(res)
print("Fetching results from ChEMBL: Done!")

df_clean = clean_DB(res_df, NP_model, int(args.NPlike_score))

wd_url = "https://query.wikidata.org/sparql"
wd_all = get_all_ik(wd_url)
wd_filtred = wd_all[wd_all["inchikey"].isin(list(df_clean.inchikey))]

df_total = df_clean.merge(
    wd_filtred[["inchikey", "wikidata_id"]], on="inchikey", how="outer"
)
df_total["wikidata_id"] = df_total["wikidata_id"].fillna("no_wikidata_match")

path_to_folder = os.path.expanduser(
    os.path.join(
        os.getcwd()
        + "/output_data/chembl/"
        + args.target_id
        + "_np_like_min_"
        + str(args.NPlike_score)
        + ".csv"
    )
)
df_total.to_csv(path_to_folder)
print(f"Finished. Results are in: {path_to_folder}")
