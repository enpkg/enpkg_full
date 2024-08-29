"""Submodule for the taxa enricher."""

from typing import Dict, List
from opentree import OT
import requests
from monolith.data.analysis_class import Analysis
from monolith.enrichers.enricher import Enricher
from monolith.data.otl_class import Match, LineageItem
from monolith.data.wikidata_ott_query_class import WikidataOTTQuery


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
    
    def enrich(self, analysis: Analysis) -> Analysis:
        """Adds taxa information to the analysis."""

        if not analysis.is_source_taxon_defined():
            return analysis

        # We retrieve OTT matches for the source taxon

        genus, species = analysis.genus_and_species

        ott_match: Dict = OT.tnrs_match(
            [f"{genus} {species}"],
            context_name=None,
            do_approximate_matching=True,
            include_suppressed=False
        ).response_dict

        assert "results" in ott_match, "No results in the OTT match"

        ott_match_results = ott_match["results"][0]

        assert "matches" in ott_match_results, f"No matches in the OTT match results searching for '{genus} {species}'"

        matches: List[Match] = [
            Match.from_dict(match)
            for match in ott_match_results["matches"]
        ]

        if len(matches) == 0:
            return analysis

        analysis.extend_ott_matches(matches)

        # We retrieve the upper taxon information for each match
        for match in matches:
            match.set_lineage(
                LineageItem.from_dict(OT.taxon_info(match.ott_id, include_lineage=True).response_dict)
            )

       # Fetch Wikidata information for each match
        
        for match in matches:
            r = requests.get(self.WIKIDATA_ENDPOINT, params={"format": "json", "query": self.WIKIDATA_QUERY_TEMPLATE.format(ott_id=match.ott_id)}, timeout=10)

            if r.status_code != 200:
                continue

            match.set_wikidata(WikidataOTTQuery.from_dict(r.json()))

        return analysis