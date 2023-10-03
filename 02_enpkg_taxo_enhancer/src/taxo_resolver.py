"""This module contains the functions to perform taxonomic name resolution using the OpenTree Taxonomic Name Resolution Service."""
from typing import List, Type
import compress_json
import numpy as np
import pandas as pd
from opentree import OT
from pandas import json_normalize


from .abstract_taxon_metadata import AbstractTaxonMetadata, OTLOutput


def taxonomic_name_resolution_service_lookup(
    # species: str, 
    taxon_name: str,
    path_to_results_folders: str, 
    project_name: str
):
    """Fetches the taxonomic information for a given species name using the OpenTree Taxonomic Name Resolution Service.

    Parameters
    ----------
    species : str
        The species name to be resolved.
    path_to_results_folders : str
        The path to the results folder.
    project_name : str
        The name of the project.

    """
    # Taxonomic Name Resolution Service lookup
    species_tnrs_matched = OT.tnrs_match(
        # species,
        names = taxon_name,
        context_name=None,
        do_approximate_matching=True,
        include_suppressed=False,
    )

    path = path_to_results_folders + project_name + "_species.json"
    compress_json.dump(
        species_tnrs_matched.response_dict,
        path=path,
        json_kwargs=dict(indent=2, sort_keys=True),
    )


def get_taxonomic_information_from_open_tree_of_life_id(
    ott_list: List[int], path_to_results_folders: str, project_name: str
):
    """Fetches the taxonomic information for a given OpenTree of Life ID using the OpenTree Taxonomic Name Resolution Service.

    Parameters
    ----------
    ott_list : List[int]
        The list of OpenTree of Life IDs to be resolved.
    path_to_results_folders : str
        The path to the results folder.
    project_name : str
        The name of the project.

    """
    path = path_to_results_folders + project_name + "_taxon_info.json"

    compress_json.dump(
        [OT.taxon_info(ott, include_lineage=True).response_dict for ott in ott_list],
        path=path,
        json_kwargs=dict(indent=2, sort_keys=True),
    )


def taxa_lineage_appender(
    taxon : Type[AbstractTaxonMetadata],
    # samples_metadata: pd.DataFrame,
    # organism_header: str,
    do_taxo_resolving: bool,
    path_to_results_folders: str,
    project_name: str,
) -> OTLOutput:
    """Fetches the taxonomic information for a given OpenTree of Life ID using the OpenTree Taxonomic Name Resolution Service.

    Parameters
    ----------
    samples_metadata : pd.DataFrame
        The metadata dataframe.
    organism_header : str
        The name of the column containing the organism names.
    do_taxo_resolving : bool
        Whether to perform taxonomic name resolution.
    path_to_results_folders : str
        The path to the results folder.
    project_name : str
        The name of the project.

    """
    # Now we want to get the taxonomic information for each of the samples
    # so we first want to extract the species information from the metadata file

    
    # samples_metadata[organism_header].dropna(inplace=True)
    # samples_metadata[organism_header] = samples_metadata[organism_header].str.lower()
    # species = samples_metadata[organism_header].unique()

    taxon_name = taxon.get_taxon_name()

    if do_taxo_resolving:
        taxonomic_name_resolution_service_lookup(
            taxon_name, path_to_results_folders, project_name
        )

    path = path_to_results_folders + project_name + "_species.json"
    jsondic = compress_json.load(path)

    df_species_tnrs_matched = json_normalize(
        jsondic, record_path=["results", "matches"]
    )

    # We then want to match with the accepted name instead of the synonym in case both are present.
    # We thus order by matched_name and then by is_synonym status prior to returning the first row.
    if len(df_species_tnrs_matched) == 0:
        samples_metadata["matched_name"] = "None"
    else:
        df_species_tnrs_matched.sort_values(
            ["search_string", "is_synonym"], axis=0, inplace=True
        )
        df_species_tnrs_matched_unique = df_species_tnrs_matched.drop_duplicates(
            "search_string", keep="first"
        )

        print(df_species_tnrs_matched_unique.columns)

        otl_output = OTLOutput(
            ott_id=df_species_tnrs_matched_unique["taxon.ott_id"],
            domain=df_species_tnrs_matched_unique["taxon.domain"],
            kingdom=df_species_tnrs_matched_unique["taxon.kingdom"],
            phylum=df_species_tnrs_matched_unique["taxon.phylum"],
            class_=df_species_tnrs_matched_unique["taxon.class"],
            order=df_species_tnrs_matched_unique["taxon.order"],
            family=df_species_tnrs_matched_unique["taxon.family"],
            tribe=df_species_tnrs_matched_unique["taxon.tribe"],
            genus=df_species_tnrs_matched_unique["taxon.genus"],
            unique_name=df_species_tnrs_matched_unique["taxon.unique_name"],
        )

        return otl_output

        # both df are finally merged
        merged_df = pd.merge(
            samples_metadata,
            df_species_tnrs_matched_unique,
            how="left",
            left_on=organism_header,
            right_on="search_string",
            indicator=True,
        )

        # converting 'ott_ids' from float to int (check the astype('Int64') whic will work while the astype('int') won't see https://stackoverflow.com/a/54194908)
        merged_df["taxon.ott_id"] = merged_df["taxon.ott_id"].astype("Int64")

        # However, we then need to put them back to
        ott_list = list(merged_df["taxon.ott_id"].dropna().astype("int"))

        if do_taxo_resolving:
            get_taxonomic_information_from_open_tree_of_life_id(
                ott_list, path_to_results_folders, project_name
            )

        path = path_to_results_folders + project_name + "_taxon_info.json"
        jsondic = compress_json.load(path)

        df_tax_lineage = json_normalize(
            jsondic,
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

        # here we want to have these columns whatevere happens
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
    return samples_metadata
