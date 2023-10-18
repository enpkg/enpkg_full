"""This module contains the functions to perform taxonomic name resolution using the OpenTree Taxonomic Name Resolution Service.
It also contains function to retrieve Wikidata taxonomic information once that the taxonomic name resolution has been performed."""

from typing import Type


import numpy as np
import pandas as pd
import requests
from opentree import OT
from pandas import json_normalize


from src.classes.abstract_taxon import AbstractTaxon, OTLTaxonInfo, WDTaxonInfo


def tnrs_lookup(taxon: Type[AbstractTaxon]) -> dict:
    """Fetches the taxonomic information for a given taxon name using the OpenTree Taxonomic Name Resolution Service.

    Parameters
    ----------
    taxon : Type[AbstractTaxon]
        The taxon to be resolved.

    Returns
    -------
    taxon_tnrs_matched.response_dict : dict
        The response of the OT call.
    """

    # The taxon name is fetched from the taxon object

    taxon_name = taxon.get_taxon_name()

    # Taxonomic Name Resolution Service lookup
    taxon_tnrs_matched = OT.tnrs_match(
        names=[taxon_name],
        context_name=None,
        do_approximate_matching=True,
        include_suppressed=False,
    )

    # The response of the OT call is returned
    return taxon_tnrs_matched.response_dict


def otl_taxon_lineage_appender(taxon: Type[AbstractTaxon]) -> OTLTaxonInfo:
    """Fetches the taxonomic information for a given taxon name using the OpenTree Taxonomic Name Resolution Service."""
    jsondic = tnrs_lookup(taxon)

    df_species_tnrs_matched = json_normalize(
        jsondic, record_path=["results", "matches"]
    )

    # We then want to match with the accepted name instead of the synonym in case both are present.
    # We thus order by matched_name and then by is_synonym status prior to returning the first row.

    df_species_tnrs_matched.sort_values(
        ["search_string", "is_synonym"], axis=0, inplace=True
    )
    merged_df = df_species_tnrs_matched.drop_duplicates("search_string", keep="first")
    # converting 'ott_ids' from float to int (check the astype('Int64') whic will work while the astype('int') won't see https://stackoverflow.com/a/54194908)
    merged_df["taxon.ott_id"] = merged_df["taxon.ott_id"].astype("Int64")

    # However, we then need to put them back to
    ott_list = list(merged_df["taxon.ott_id"].dropna().astype("int"))

    ott_resolved = [
        OT.taxon_info(ott, include_lineage=True).response_dict for ott in ott_list
    ]

    df_tax_lineage = json_normalize(
        ott_resolved,
        record_path=["lineage"],
        meta=["ott_id", "unique_name"],
        record_prefix="sub_",
        errors="ignore",
    )

    # This keeps the last occurence of each ott_id / sub_rank grouping https://stackoverflow.com/a/41886945
    df_tax_lineage_filtered = df_tax_lineage.groupby(
        ["ott_id", "sub_rank"], as_index=False
    ).last()

    # Here we pivot long to wide to get the taxonomy
    df_tax_lineage_filtered_flat = df_tax_lineage_filtered.pivot(
        index="ott_id", columns="sub_rank", values="sub_name"
    )

    # Here we actually also want the lowertaxon (species usually) name
    df_tax_lineage_filtered_flat = pd.merge(
        df_tax_lineage_filtered_flat,
        df_tax_lineage_filtered[["ott_id", "unique_name"]],
        how="left",
        on="ott_id",
    )

    # Despite the left join ott_id are duplicated
    df_tax_lineage_filtered_flat.drop_duplicates(
        subset=["ott_id", "unique_name"], inplace=True
    )

    # here we want to have these columns whatever happens
    col_list = [
        "ott_id",
        "domain",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "tribe",
        "genus",
        "unique_name",
    ]

    df_tax_lineage_filtered_flat = df_tax_lineage_filtered_flat.reindex(
        columns=col_list, fill_value=np.NaN
    )

    # We now rename our columns of interest
    renaming_dict = {
        "domain": "query_otol_domain",
        "kingdom": "query_otol_kingdom",
        "phylum": "query_otol_phylum",
        "class": "query_otol_class",
        "order": "query_otol_order",
        "family": "query_otol_family",
        "tribe": "query_otol_tribe",
        "genus": "query_otol_genus",
        "unique_name": "query_otol_species",
    }

    df_tax_lineage_filtered_flat.rename(columns=renaming_dict, inplace=True)

    # We select columns of interest
    cols_to_keep = [
        "ott_id",
        "query_otol_domain",
        "query_otol_kingdom",
        "query_otol_phylum",
        "query_otol_class",
        "query_otol_order",
        "query_otol_family",
        "query_otol_tribe",
        "query_otol_genus",
        "query_otol_species",
    ]

    df_tax_lineage_filtered_flat = df_tax_lineage_filtered_flat[cols_to_keep]

    # We merge this back with the samplemetadata only if we have an ott.id in the merged df
    samples_metadata = pd.merge(
        merged_df[pd.notnull(merged_df["taxon.ott_id"])],
        df_tax_lineage_filtered_flat,
        how="left",
        left_on="taxon.ott_id",
        right_on="ott_id",
    )

    # We now populate the OTLTaxonInfo object

    taxon_lineage = OTLTaxonInfo(
        ott_id=samples_metadata["taxon.ott_id"],
        otol_domain=samples_metadata["query_otol_domain"],
        otol_kingdom=samples_metadata["query_otol_kingdom"],
        otol_phylum=samples_metadata["query_otol_phylum"],
        otol_class=samples_metadata["query_otol_class"],
        otol_order=samples_metadata["query_otol_order"],
        otol_family=samples_metadata["query_otol_family"],
        otol_tribe=samples_metadata["query_otol_tribe"],
        otol_genus=samples_metadata["query_otol_genus"],
        otol_species=samples_metadata["query_otol_species"],
        taxon_source=samples_metadata["taxon.source"],
        taxon_rank=samples_metadata["taxon.rank"],
        search_string=samples_metadata["search_string"],
        score=samples_metadata["score"],
        matched_name=samples_metadata["matched_name"],
        is_synonym=samples_metadata["is_synonym"],
        is_approximate_match=samples_metadata["is_approximate_match"],
    )

    return taxon_lineage


def wd_taxon_fetcher(ott_id: int) -> WDTaxonInfo:
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

    url = "https://query.wikidata.org/sparql"
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

    wd_taxon_info = WDTaxonInfo(
        wd_qid=df["qid.value"][0],
        wd_qid_url=df["wd.value"][0],
        wd_img_url=df["img.value"][0],
    )

    return wd_taxon_info
