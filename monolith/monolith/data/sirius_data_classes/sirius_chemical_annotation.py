"""Submodule providing dataclasses for representing chemical annotations from Sirius."""

from dataclasses import dataclass
from monolith.data.lotus_class import Lotus
from monolith.data.chemical_annotation import ChemicalAnnotation


@dataclass
class SiriusChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from Sirius."""

    lotus: list[Lotus]

    def lotus_annotations(self) -> list[Lotus]:
        """Return the list of Lotus annotations."""
        return self.lotus
