import pandas as pd
import numpy as np
from pandas import json_normalize
import requests
import os
from taxo_resolver import *
from pathlib import Path
import argparse
import textwrap
import yaml
import git
import opentree
from opentree import OT


from abstract_taxon import AbstractTaxon, Taxon, OTLTaxonInfo, WDTaxonInfo



def wd_taxo_fetcher_from_ott(ott_id: int) -> WDTaxonInfo:
    """This function return the Wikidata QID and an image URL for a given OTT ID."""

    # Define the SPARQL query
    query = f"""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?ott ?wd ?img
    WHERE{{
        ?wd wdt:P9157 ?ott
        OPTIONAL{{ ?wd wdt:P18 ?img }}
        VALUES ?ott {{'{ott_id}'}}
    }}
    """

    url = 'https://query.wikidata.org/sparql'
    r = requests.get(url, params={"format": "json", "query": query}, timeout=10)

    data = r.json()
    results = pd.DataFrame.from_dict(data).results.bindings
    df = json_normalize(results)
    if len(df) == 0:
        df = pd.DataFrame(
            data={
                "ott.type": [np.NaN],
                "ott.value": [np.NaN],
                "wd.type": [np.NaN],
                "wd.value": [np.NaN],
            }
        )

    # Strip the url prefix from the wd.value to get the QID
    df["qid.value"] = df["wd.value"].str.replace("http://www.wikidata.org/entity/", "")

    # Instantiate a WDTaxonInfo object

    wd_taxon_info = WDTaxonInfo(wd_qid=df["qid.value"][0], wd_qid_url=df["wd.value"][0], wd_img_url=df["img.value"][0])

    return wd_taxon_info


