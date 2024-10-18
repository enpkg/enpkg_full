"""Submodule providing dataclasses for representing MS2-level chemical annotations from ISDB."""

from typing import List, Optional
import numpy as np
from typeguard import typechecked
from monolith.data.lotus_class import (
    Lotus,
)
from monolith.data.chemical_annotation import ChemicalAnnotation
from monolith.data.otl_class import Match


class ISDBChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from ISDB."""

    lotus: Optional[List[Lotus]]
    cosine_similarity: float
    number_of_matched_peaks: int

    @typechecked
    def __init__(
        self,
        lotus: Optional[List[Lotus]],
        cosine_similarity: float,
        number_of_matched_peaks: int,
    ):
        """Initialize the ISDBChemicalAnnotation dataclass."""
        super().__init__()
        self.lotus = lotus
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks

    @typechecked
    def get_hammer_pathway_scores(self, match: Match) -> Optional[np.ndarray]:
        """Return the pathway scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        return np.mean(
            [
                lotus.structure_taxonomy_hammer_pathways
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def get_hammer_superclass_scores(self, match: Match) -> Optional[np.ndarray]:
        """Return the superclass scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        return np.mean(
            [
                lotus.structure_taxonomy_hammer_superclasses
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def get_hammer_class_scores(self, match: Match) -> Optional[np.ndarray]:
        """Return the class scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        return np.mean(
            [
                lotus.structure_taxonomy_hammer_classes
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def lotus_annotations(self) -> Optional[List[Lotus]]:
        """Return the list of Lotus annotations."""
        return self.lotus
