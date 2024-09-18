"""Submodule providing dataclasses for representing chemical annotations from Sirius."""

from dataclasses import dataclass
from typing import List
from monolith.data.lotus_class import Lotus
from monolith.data.chemical_annotation import ChemicalAnnotation


@dataclass
class SiriusChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from Sirius."""

    lotus: List[Lotus]

    def lotus_annotations(self) -> List[Lotus]:
        """Return the list of Lotus annotations."""
        return self.lotus
