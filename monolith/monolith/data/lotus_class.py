"""Data class representing the key information of a LOTUS entry."""

from dataclasses import dataclass
import pandas as pd


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
    organism_taxonomy_01domain: str
    organism_taxonomy_02kingdom: str
    organism_taxonomy_03phylum: str
    organism_taxonomy_04class: str
    organism_taxonomy_05order: str
    organism_taxonomy_06family: str
    organism_taxonomy_07tribe: str
    organism_taxonomy_08genus: str
    organism_taxonomy_09species: str
    organism_taxonomy_10varietas: str
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
            organism_taxonomy_01domain=series["organism_taxonomy_01domain"],
            organism_taxonomy_02kingdom=series["organism_taxonomy_02kingdom"],
            organism_taxonomy_03phylum=series["organism_taxonomy_03phylum"],
            organism_taxonomy_04class=series["organism_taxonomy_04class"],
            organism_taxonomy_05order=series["organism_taxonomy_05order"],
            organism_taxonomy_06family=series["organism_taxonomy_06family"],
            organism_taxonomy_07tribe=series["organism_taxonomy_07tribe"],
            organism_taxonomy_08genus=series["organism_taxonomy_08genus"],
            organism_taxonomy_09species=series["organism_taxonomy_09species"],
            organism_taxonomy_10varietas=series["organism_taxonomy_10varietas"],
            reference_wikidata=series["reference_wikidata"],
            reference_doi=series["reference_doi"],
            manual_validation=series["manual_validation"],
        )

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the InChIKey."""
        return self.structure_inchikey[:14]
