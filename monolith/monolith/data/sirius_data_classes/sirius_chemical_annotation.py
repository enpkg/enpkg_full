"""Submodule providing dataclasses for representing chemical annotations from Sirius."""

from dataclasses import dataclass
from monolith.data.lotus_class import Lotus
from monolith.data.chemical_annotation import ChemicalAnnotation
from typing import Optional


@dataclass
class SiriusChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from Sirius."""

    lotus: Optional[list[Lotus]]
    confidence_rank: int
    structure_per_id_rank: int
    formula_rank: int
    adducts_number: int
    predicted_fps_number: int
    confidence_score: float
    csi_finger_id_score: float
    zodiac_score: float
    sirius_score: float
    molecular_formula: str
    adduct: str
    inchikey2d: str
    inchi: str
    name: str
    smiles: str
    xlogp: float
    pubchemids: str
    links: str
    dbflags: str
    ion_mass: float
    retention_time_in_seconds: float
    sirius_id: int
    feature_id: int

    @classmethod
    def setup_sirius_chemical_annotation_columns(cls, columns: list[str]):
        """Setup the columns for the SiriusChemicalAnnotation."""
        cls._columns = {column: i for i, column in enumerate(columns)}

    @classmethod
    def from_pandas_series(
        cls,
        series: list[Any]
    ) -> "SiriusChemicalAnnotation":
    """Create a SiriusChemicalAnnotation from a pandas Series."""

    # We normalize the NaN values to None
    series = [None if pd.isna(value) else value for value in series]

    return cls(
        lotus=None,
        confidence_rank=series[cls._columns["confidence_rank"]],
        structure_per_id_rank=series[cls._columns["structure_per_id_rank"]],
        formula_rank=series[cls._columns["formula_rank"]],
        adducts_number=series[cls._columns["adducts_number"]],
        predicted_fps_number=series[cls._columns["predicted_fps_number"]],
        confidence_score=series[cls._columns["confidence_score"]],
        csi_finger_id_score=series[cls._columns["csi_finger_id_score"]],
        zodiac_score=series[cls._columns["zodiac_score"]],
        sirius_score=series[cls._columns["sirius_score"]],
        molecular_formula=series[cls._columns["molecular_formula"]],
        adduct=series[cls._columns["adduct"]],
        inchikey2d=series[cls._columns["inchikey2d"]],
        inchi=series[cls._columns["inchi"]],
        name=series[cls._columns["name"]],
        smiles=series[cls._columns["smiles"]],
        xlogp=series[cls._columns["xlogp"]],
        pubchemids=series[cls._columns["pubchemids"]],
        links=series[cls._columns["links"]],
        dbflags=series[cls._columns["dbflags"]],
        ion_mass=series[cls._columns["ion_mass"]],
        retention_time_in_seconds=series[cls._columns["retention_time_in_seconds"]],
        sirius_id=series[cls._columns["id"]],
        feature_id=series[cls._columns["feature_id"]]
    )

    def lotus_annotations(self) -> Optional[list[Lotus]]:
        """Return the list of Lotus annotations."""
        return self.lotus
