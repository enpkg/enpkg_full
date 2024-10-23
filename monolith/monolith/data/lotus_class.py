"""Data class representing the key information of a LOTUS entry."""

from typing import List, Any, Dict
from dataclasses import dataclass
from typeguard import typechecked
import pandas as pd
from monolith.data.otl_class import Match

MAXIMAL_TAXONOMICAL_SCORE: float = 8.0

@dataclass
class Lotus:
    """Data class representing the key information of a LOTUS entry."""

    structure_wikidata: str
    structure_inchikey: str
    structure_inchi: str
    structure_smiles: str
    structure_molecular_formula: str
    structure_exact_mass: float
    structure_xlogp: float
    structure_smiles_2d: str
    structure_cid: int
    structure_name_iupac: str
    structure_name_traditional: str
    structure_stereocenters_total: int
    structure_stereocenters_unspecified: int
    structure_taxonomy_hammer_pathways: pd.Series
    structure_taxonomy_hammer_superclasses: pd.Series
    structure_taxonomy_hammer_classes: pd.Series
    structure_taxonomy_classyfire_chemontid: str
    structure_taxonomy_classyfire_01kingdom: str
    structure_taxonomy_classyfire_02superclass: str
    structure_taxonomy_classyfire_03class: str
    structure_taxonomy_classyfire_04directparent: str
    organism_wikidata: str
    organism_name: str
    organism_taxonomy_gbifid: int
    organism_taxonomy_ncbiid: int
    organism_taxonomy_ottid: int
    domain: str
    kingdom: str
    phylum: str
    klass: str
    order: str
    family: str
    tribe: str
    genus: str
    species: str
    varietas: str
    reference_wikidata: str
    reference_doi: str
    manual_validation: bool

    @classmethod
    @typechecked
    def setup_lotus_columns(cls, columns: List[str]):
        """Set up the columns of the LOTUS DataFrame."""
        cls._columns = {column: i for i, column in enumerate(columns)}

    @classmethod
    @typechecked
    def from_pandas_series(
        cls,
        series: List[Any],
        pathways: pd.Series,
        superclasses: pd.Series,
        classes: pd.Series,
    ) -> "Lotus":
        """Create a Lotus object from a pandas Series."""

        # We normalize the NaN values to None
        series = [None if pd.isna(value) else value for value in series]

        return cls(
            structure_wikidata=series[Lotus._columns["structure_wikidata"]],
            structure_inchikey=series[Lotus._columns["structure_inchikey"]],
            structure_inchi=series[Lotus._columns["structure_inchi"]],
            structure_smiles=series[Lotus._columns["structure_smiles"]],
            structure_molecular_formula=series[
                Lotus._columns["structure_molecular_formula"]
            ],
            structure_exact_mass=series[Lotus._columns["structure_exact_mass"]],
            structure_xlogp=series[Lotus._columns["structure_xlogp"]],
            structure_smiles_2d=series[Lotus._columns["structure_smiles_2D"]],
            structure_cid=series[Lotus._columns["structure_cid"]],
            structure_name_iupac=series[Lotus._columns["structure_nameIupac"]],
            structure_name_traditional=series[
                Lotus._columns["structure_nameTraditional"]
            ],
            structure_taxonomy_hammer_pathways=pathways,
            structure_taxonomy_hammer_superclasses=superclasses,
            structure_taxonomy_hammer_classes=classes,
            structure_stereocenters_total=series[
                Lotus._columns["structure_stereocenters_total"]
            ],
            structure_stereocenters_unspecified=series[
                Lotus._columns["structure_stereocenters_unspecified"]
            ],
            structure_taxonomy_classyfire_chemontid=series[
                Lotus._columns["structure_taxonomy_classyfire_chemontid"]
            ],
            structure_taxonomy_classyfire_01kingdom=series[
                Lotus._columns["structure_taxonomy_classyfire_01kingdom"]
            ],
            structure_taxonomy_classyfire_02superclass=series[
                Lotus._columns["structure_taxonomy_classyfire_02superclass"]
            ],
            structure_taxonomy_classyfire_03class=series[
                Lotus._columns["structure_taxonomy_classyfire_03class"]
            ],
            structure_taxonomy_classyfire_04directparent=series[
                Lotus._columns["structure_taxonomy_classyfire_04directparent"]
            ],
            organism_wikidata=series[Lotus._columns["organism_wikidata"]],
            organism_name=series[Lotus._columns["organism_name"]],
            organism_taxonomy_gbifid=series[Lotus._columns["organism_taxonomy_gbifid"]],
            organism_taxonomy_ncbiid=series[Lotus._columns["organism_taxonomy_ncbiid"]],
            organism_taxonomy_ottid=series[Lotus._columns["organism_taxonomy_ottid"]],
            domain=series[Lotus._columns["organism_taxonomy_01domain"]],
            kingdom=series[Lotus._columns["organism_taxonomy_02kingdom"]],
            phylum=series[Lotus._columns["organism_taxonomy_03phylum"]],
            klass=series[Lotus._columns["organism_taxonomy_04class"]],
            order=series[Lotus._columns["organism_taxonomy_05order"]],
            family=series[Lotus._columns["organism_taxonomy_06family"]],
            tribe=series[Lotus._columns["organism_taxonomy_07tribe"]],
            genus=series[Lotus._columns["organism_taxonomy_08genus"]],
            species=series[Lotus._columns["organism_taxonomy_09species"]],
            varietas=series[Lotus._columns["organism_taxonomy_10varietas"]],
            reference_wikidata=series[Lotus._columns["reference_wikidata"]],
            reference_doi=series[Lotus._columns["reference_doi"]],
            manual_validation=series[Lotus._columns["manual_validation"]],
        )

    def __hash__(self) -> int:
        """Return the hash of the InChIKey."""
        return hash((
            self.structure_inchikey,
            self.organism_taxonomy_ottid
        ))

    def __eq__(self, other: object) -> bool:
        """Return whether two LOTUS entries are equal."""
        if not isinstance(other, Lotus):
            return False

        return (
            self.structure_inchikey == other.structure_inchikey
            and self.organism_taxonomy_ottid == other.organism_taxonomy_ottid
        )

    def to_dict(self) -> Dict[str, Any]:
        """Returns the principal informations of the LOTUS entry as a dictionary.
        
        Implementative details
        ----------------------
        We solely maintain the features that can be represented
        in a tabular form. Complex features such as the scores are,
        therefore, excluded.
        """
        return {
            "structure_inchikey": self.structure_inchikey,
            "structure_inchi": self.structure_inchi,
            "structure_smiles": self.structure_smiles,
            "structure_molecular_formula": self.structure_molecular_formula,
            "structure_exact_mass": self.structure_exact_mass,
            "structure_xlogp": self.structure_xlogp,
            "structure_smiles_2d": self.structure_smiles_2d,
            "structure_cid": self.structure_cid,
            "structure_name_iupac": self.structure_name_iupac,
            "structure_name_traditional": self.structure_name_traditional,
            "structure_stereocenters_total": self.structure_stereocenters_total,
            "structure_stereocenters_unspecified": self.structure_stereocenters_unspecified,
            "structure_taxonomy_classyfire_chemontid": self.structure_taxonomy_classyfire_chemontid,
            "structure_taxonomy_classyfire_01kingdom": self.structure_taxonomy_classyfire_01kingdom,
            "structure_taxonomy_classyfire_02superclass": self.structure_taxonomy_classyfire_02superclass,
            "structure_taxonomy_classyfire_03class": self.structure_taxonomy_classyfire_03class,
            "structure_taxonomy_classyfire_04directparent": self.structure_taxonomy_classyfire_04directparent,
            "organism_wikidata": self.organism_wikidata,
            "organism_name": self.organism_name,
            "organism_taxonomy_gbifid": self.organism_taxonomy_gbifid,
            "organism_taxonomy_ncbiid": self.organism_taxonomy_ncbiid,
            "organism_taxonomy_ottid": self.organism_taxonomy_ottid,
            "domain": self.domain,
            "kingdom": self.kingdom,
            "phylum": self.phylum,
            "klass": self.klass,
            "order": self.order,
            "family": self.family,
            "tribe": self.tribe,
            "genus": self.genus,
            "species": self.species,
            "varietas": self.varietas,
            "reference_wikidata": self.reference_wikidata,
            "reference_doi": self.reference_doi,
            "manual_validation": self.manual_validation,
        }

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the InChIKey."""
        return self.structure_inchikey[:14]

    @typechecked
    def taxonomical_similarity_with_otl_match(self, match: Match) -> float:
        """Calculate the taxonomical similarity with an OTL match.

        Implementative details
        ----------------------
        The taxonomical similarity is calculated as the number of shared taxonomic ranks
        between the LOTUS organism and the OTL match organism. The ranks are ordered from
        domain to species, and the similarity is calculated as the number of ranks that
        are the same between the two organisms.
        """
        if self.species == match.species:
            return 8.0

        if self.genus == match.genus:
            return 7.0

        if self.family == match.family:
            return 6.0

        if self.order == match.order:
            return 5.0

        if self.klass == match.klass:
            return 4.0

        if self.phylum == match.phylum:
            return 3.0

        if self.kingdom == match.kingdom:
            return 2.0

        if self.domain == match.domain:
            return 1.0

        return 0.0

    @typechecked
    def normalized_taxonomical_similarity_with_otl_match(self, match: Match) -> float:
        """Calculate the normalized taxonomical similarity with an OTL match.

        Implementative details
        ----------------------
        The normalized taxonomical similarity is calculated as the taxonomical similarity
        divided by the maximum possible similarity (8).
        """
        match_score = self.taxonomical_similarity_with_otl_match(match)
        assert (
            match_score <= MAXIMAL_TAXONOMICAL_SCORE
        ), f"Expected a maximal score of {MAXIMAL_TAXONOMICAL_SCORE}, got {match_score}."
        return match_score / MAXIMAL_TAXONOMICAL_SCORE
