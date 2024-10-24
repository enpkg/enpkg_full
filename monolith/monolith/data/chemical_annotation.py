"""Module to store a chemical annotation."""

from abc import abstractmethod, ABC
from typing import Optional
from monolith.data.lotus_class import Lotus
from monolith.data.otl_class import Match


class ChemicalAnnotation(ABC):
    """Class to store a chemical annotation."""

    @abstractmethod
    def lotus_annotations(self) -> Optional[list[Lotus]]:
        """Return the LOTUS annotations for the annotation."""

    def has_lotus_entries(self) -> bool:
        """Return whether the annotation has Lotus entries."""
        return self.lotus_annotations() is not None

    def maximal_normalized_taxonomical_similarity(
        self, match: Match
    ) -> Optional[float]:
        """Return the maximal normalized taxonomical similarity of the adduct."""
        if not self.has_lotus_entries():
            return None

        return max(
            lotus.normalized_taxonomical_similarity_with_otl_match(match)
            for lotus in self.lotus_annotations()
        )
