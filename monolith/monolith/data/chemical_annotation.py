"""Module to store a chemical annotation."""

from abc import abstractmethod, ABC
from typing import List
from monolith.data.lotus_class import Lotus


class ChemicalAnnotation(ABC):
    """Class to store a chemical annotation."""

    @abstractmethod
    def lotus_annotations(self) -> List[Lotus]:
        """Return the LOTUS annotations for the annotation."""
