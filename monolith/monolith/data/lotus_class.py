"""Data class representing the key information of a LOTUS entry."""

from dataclasses import dataclass
import pandas as pd
from monolith.data.otl_class import Match


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
    structure_taxonomy_npclassifier_01pathway: str
    structure_taxonomy_npclassifier_02superclass: str
    structure_taxonomy_npclassifier_03class: str
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

    @staticmethod
    def from_pandas_series(series: pd.Series) -> "Lotus":
        """Create a Lotus object from a pandas Series."""
        return Lotus(
            structure_wikidata=series["structure_wikidata"],
            structure_inchikey=series["structure_inchikey"],
            structure_inchi=series["structure_inchi"],
            structure_smiles=series["structure_smiles"],
            structure_molecular_formula=series["structure_molecular_formula"],
            structure_exact_mass=series["structure_exact_mass"],
            structure_xlogp=series["structure_xlogp"],
            structure_smiles_2d=series["structure_smiles_2D"],
            structure_cid=series["structure_cid"],
            structure_name_iupac=series["structure_nameIupac"],
            structure_name_traditional=series["structure_nameTraditional"],
            structure_stereocenters_total=series["structure_stereocenters_total"],
            structure_stereocenters_unspecified=series[
                "structure_stereocenters_unspecified"
            ],
            structure_taxonomy_npclassifier_01pathway=series[
                "structure_taxonomy_npclassifier_01pathway"
            ],
            structure_taxonomy_npclassifier_02superclass=series[
                "structure_taxonomy_npclassifier_02superclass"
            ],
            structure_taxonomy_npclassifier_03class=series[
                "structure_taxonomy_npclassifier_03class"
            ],
            structure_taxonomy_classyfire_chemontid=series[
                "structure_taxonomy_classyfire_chemontid"
            ],
            structure_taxonomy_classyfire_01kingdom=series[
                "structure_taxonomy_classyfire_01kingdom"
            ],
            structure_taxonomy_classyfire_02superclass=series[
                "structure_taxonomy_classyfire_02superclass"
            ],
            structure_taxonomy_classyfire_03class=series[
                "structure_taxonomy_classyfire_03class"
            ],
            structure_taxonomy_classyfire_04directparent=series[
                "structure_taxonomy_classyfire_04directparent"
            ],
            organism_wikidata=series["organism_wikidata"],
            organism_name=series["organism_name"],
            organism_taxonomy_gbifid=series["organism_taxonomy_gbifid"],
            organism_taxonomy_ncbiid=series["organism_taxonomy_ncbiid"],
            organism_taxonomy_ottid=series["organism_taxonomy_ottid"],
            domain=series["organism_taxonomy_01domain"],
            kingdom=series["organism_taxonomy_02kingdom"],
            phylum=series["organism_taxonomy_03phylum"],
            klass=series["organism_taxonomy_04class"],
            order=series["organism_taxonomy_05order"],
            family=series["organism_taxonomy_06family"],
            tribe=series["organism_taxonomy_07tribe"],
            genus=series["organism_taxonomy_08genus"],
            species=series["organism_taxonomy_09species"],
            varietas=series["organism_taxonomy_10varietas"],
            reference_wikidata=series["reference_wikidata"],
            reference_doi=series["reference_doi"],
            manual_validation=series["manual_validation"],
        )

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the InChIKey."""
        return self.structure_inchikey[:14]

    def taxonomical_similarity_with_otl_match(self, match: Match) -> int:
        """Calculate the taxonomical similarity with an OTL match.
        
        Implementative details
        ----------------------
        The taxonomical similarity is calculated as the number of shared taxonomic ranks
        between the LOTUS organism and the OTL match organism. The ranks are ordered from
        domain to species, and the similarity is calculated as the number of ranks that
        are the same between the two organisms.
        """
        if self.species == match.species:
            return 8

        if self.genus == match.genus:
            return 7

        if self.family == match.family:
            return 6

        if self.order == match.order:
            return 5

        if self.klass == match.klass:
            return 4

        if self.phylum == match.phylum:
            return 3

        if self.kingdom == match.kingdom:
            return 2

        if self.domain == match.domain:
            return 1

        return 0