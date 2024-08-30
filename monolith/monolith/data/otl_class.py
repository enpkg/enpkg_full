from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from monolith.data.wikidata_ott_query_class import WikidataOTTQuery


@dataclass
class Taxon:
    """
    Represents the taxonomic details of a match.

    Attributes:
        flags (List[str]): A list of flags associated with the taxon.
        is_suppressed (bool): Indicates whether the taxon is suppressed.
        is_suppressed_from_synth (bool): Indicates whether the taxon is suppressed from synthesis.
        name (str): The scientific name of the taxon.
        ott_id (int): The Open Tree Taxonomy (OTT) identifier for the taxon.
        rank (str): The taxonomic rank of the taxon (e.g., species, genus).
        source (str): The source of the taxon information.
        synonyms (List[str]): A list of synonyms for the taxon.
        tax_sources (List[str]): A list of taxonomic sources.
        unique_name (str): A unique name for the taxon.
        lineage (List[LineageItem]): A list representing the lineage hierarchy for the taxon.
    """

    flags: List[str]
    is_suppressed: bool
    is_suppressed_from_synth: bool
    name: str
    ott_id: int
    rank: str
    source: str
    synonyms: List[str]
    tax_sources: List[str]
    unique_name: str
    wikidata: Optional[WikidataOTTQuery] = None

    def set_wikidata(self, wikidata: WikidataOTTQuery) -> None:
        """Sets the Wikidata information for the taxon."""
        assert isinstance(
            wikidata, WikidataOTTQuery
        ), "wikidata must be an instance of WikidataOTTQuery"
        assert (
            wikidata.ott == self.ott_id
        ), f"OTT ID mismatch between taxon ({self.ott_id}) and Wikidata information ({wikidata.ott})"
        self.wikidata = wikidata

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Taxon":
        """
        Creates an instance of Taxon from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing taxon data.

        Returns:
            Taxon: An instance of the Taxon class.

        Raises:
            ValueError: If any required field is missing from the data.
        """
        try:
            return Taxon(
                flags=data.get("flags", []),
                is_suppressed=data["is_suppressed"],
                is_suppressed_from_synth=data["is_suppressed_from_synth"],
                name=data["name"],
                ott_id=int(data["ott_id"]),
                rank=data["rank"],
                source=data["source"],
                synonyms=data.get("synonyms", []),
                tax_sources=data.get("tax_sources", []),
                unique_name=data["unique_name"],
            )
        except KeyError as e:
            raise ValueError("Missing required field in Taxon data") from e


@dataclass
class LineageItem:
    """Data class representing a lineage item."""

    flags: List[str]
    is_suppressed: bool
    is_suppressed_from_synth: bool
    taxa: List[Taxon]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "LineageItem":
        """Creates an instance of LineageItem from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing lineage item data.

        Returns:
            LineageItem: An instance of the LineageItem class.

        Raises:
            ValueError: If any required field is missing from the data.
        """

        try:
            return LineageItem(
                flags=data.get("flags", []),
                is_suppressed=data["is_suppressed"],
                is_suppressed_from_synth=data["is_suppressed_from_synth"],
                taxa=[Taxon.from_dict(taxon_data) for taxon_data in data["lineage"]],
            )
        except KeyError as e:
            raise ValueError("Missing required field in LineageItem data") from e


@dataclass
class Match:
    """
    Represents a single match result for a search query.

    Attributes:
        is_approximate_match (bool): Indicates if the match is an approximate match.
        is_synonym (bool): Indicates if the match is a synonym.
        matched_name (str): The name that was matched.
        nomenclature_code (str): The nomenclature code (e.g., ICN).
        score (float): The match score.
        search_string (str): The original search string.
        taxon (Taxon): The taxon associated with the match.
    """

    is_approximate_match: bool
    is_synonym: bool
    matched_name: str
    nomenclature_code: str
    score: float
    search_string: str
    taxon: Taxon
    lineage: Optional[LineageItem] = None

    def _taxonomical_rank(self, rank: str) -> Optional[str]:
        """Returns the taxonomical rank of the taxon."""
        assert self.lineage is not None, "Lineage is not set for the match"

        for taxon in self.lineage.taxa:
            if taxon.rank == rank:
                return taxon.name

        return None
        
    @property
    def domain(self) -> Optional[str]:
        """Returns the lineage entry containing the domain."""
        return self._taxonomical_rank("domain")
    
    @property
    def kingdom(self) -> Optional[str]:
        """Returns the lineage entry containing the kingdom."""
        return self._taxonomical_rank("kingdom")

    @property
    def phylum(self) -> Optional[str]:
        """Returns the lineage entry containing the phylum."""
        return self._taxonomical_rank("phylum")

    @property
    def klass(self) -> Optional[str]:
        """Returns the lineage entry containing the class."""
        return self._taxonomical_rank("class")

    @property
    def order(self) -> Optional[str]:
        """Returns the lineage entry containing the order."""
        return self._taxonomical_rank("order")
    
    @property
    def family(self) -> Optional[str]:
        """Returns the lineage entry containing the family."""
        return self._taxonomical_rank("family")

    @property
    def genus(self) -> Optional[str]:
        """Returns the lineage entry containing the genus."""
        return self._taxonomical_rank("genus")
    
    @property
    def species(self) -> Optional[str]:
        """Returns the lineage entry containing the species."""
        return self._taxonomical_rank("species")
    

    @property
    def ott_id(self) -> int:
        """Returns the OTT ID of the taxon."""
        return self.taxon.ott_id

    def set_wikidata(self, wikidata: WikidataOTTQuery) -> None:
        """Sets the Wikidata information for the match."""
        self.taxon.set_wikidata(wikidata)

    def set_lineage(self, lineage: LineageItem) -> None:
        """Sets the lineage for the match."""
        self.lineage = lineage

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Match":
        """
        Creates an instance of Match from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary containing match data.

        Returns:
            Match: An instance of the Match class.

        Raises:
            ValueError: If any required field is missing from the data or if there is a type mismatch.
        """
        try:
            taxon_data = data["taxon"]
            return Match(
                is_approximate_match=data["is_approximate_match"],
                is_synonym=data["is_synonym"],
                matched_name=data["matched_name"],
                nomenclature_code=data["nomenclature_code"],
                score=data["score"],
                search_string=data["search_string"],
                taxon=Taxon.from_dict(taxon_data),
            )
        except KeyError as e:
            raise ValueError("Missing required field in Match data") from e
        except TypeError as e:
            raise ValueError("Invalid data type encountered in Match data") from e
