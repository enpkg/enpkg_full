"""Submodule for the taxa enricher."""

from typing import Dict
from opentree import OT
import requests
from monolith.data.analysis import Analysis
from monolith.enrichers.enricher import Enricher
from monolith.data.otl_class import Match, LineageItem
from monolith.data.wikidata_ott_query_class import WikidataOTTQuery
from monolith.exceptions import EnrichmentError


class TaxaEnricher(Enricher):
    """Enricher that adds taxa information to the analysis."""

    WIKIDATA_ENDPOINT: str = "https://query.wikidata.org/sparql"
    WIKIDATA_QUERY_TEMPLATE: str = """
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?ott ?wd ?img
    WHERE{{
        ?wd wdt:P9157 ?ott
        OPTIONAL{{ ?wd wdt:P18 ?img }}
        VALUES ?ott {{'{ott_id}'}}
    }}
    """

    def __init__(self):
        """Initializes the enricher."""

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "Taxonomical Enricher"

    def retrieve_matches(self, genus: str, species: str) -> list[Match]:
        """Retrieves OTT matches for the source taxon."""

        ott_match: Dict = OT.tnrs_match(
            [f"{genus} {species}"],
            context_name=None,
            do_approximate_matching=True,
            include_suppressed=False,
        ).response_dict

        if "results" not in ott_match:
            raise EnrichmentError(f"No OTT results found searching for '{genus} {species}'")

        ott_match_results = ott_match["results"][0]

        if "matches" not in ott_match_results:
            raise EnrichmentError(f"No matches in the OTT match results searching for '{genus} {species}'")

        matches: list[Match] = [
            Match.from_dict(match) for match in ott_match_results["matches"]
        ]

        if len(matches) == 0:
            return []

        # We retrieve the upper taxon information for each match
        for match in matches:
            match.set_lineage(
                LineageItem.from_dict(
                    OT.taxon_info(match.ott_id, include_lineage=True).response_dict
                )
            )
        

        # Fetch Wikidata information for each match

        for match in matches:
            r = requests.get(
                self.WIKIDATA_ENDPOINT,
                params={
                    "format": "json",
                    "query": self.WIKIDATA_QUERY_TEMPLATE.format(ott_id=match.ott_id),
                },
                timeout=10,
            )

            if r.status_code != 200:
                continue

            match.set_wikidata(WikidataOTTQuery.from_dict(r.json()))

        return matches

    def enrich(self, genus: str, species: str) -> list[Match]:
        """Now only takes strings and returns data."""
        return self.retrieve_matches(genus, species)
