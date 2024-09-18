"""Submodule providing dataclasses for representing MS2-level chemical annotations from ISDB."""

from dataclasses import dataclass
from typing import List
from monolith.data.lotus_class import Lotus
from monolith.data.chemical_annotation import ChemicalAnnotation


@dataclass
class ISDBChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from ISDB."""

    lotus: List[Lotus]
    cosine_similarity: float
    number_of_matched_peaks: int

    def lotus_annotations(self) -> List[Lotus]:
        """Return the list of Lotus annotations."""
        return self.lotus
