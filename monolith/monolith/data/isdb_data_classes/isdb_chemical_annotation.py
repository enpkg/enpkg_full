"""Submodule providing dataclasses for representing MS2-level chemical annotations from ISDB."""

from typing import List
import numpy as np
from monolith.data.lotus_class import (
    Lotus,
    NUMBER_OF_NPC_PATHWAYS,
    NUMBER_OF_NPC_CLASSES,
    NUMBER_OF_NPC_SUPERCLASSES,
)
from monolith.data.chemical_annotation import ChemicalAnnotation
from monolith.data.otl_class import Match


class ISDBChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from ISDB."""

    lotus: List[Lotus]
    cosine_similarity: float
    number_of_matched_peaks: int

    def __init__(
        self, lotus: List[Lotus], cosine_similarity: float, number_of_matched_peaks: int
    ):
        """Initialize the ISDBChemicalAnnotation dataclass."""
        super().__init__()
        self.lotus = lotus
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks

    def get_npc_pathway_scores(self, match: Match) -> np.ndarray:
        """Return the pathway scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return np.zeros(
                (NUMBER_OF_NPC_PATHWAYS,),
            )

        return np.mean(
            [
                lotus.one_hot_encoded_npc_pathway
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def get_npc_superclass_scores(self, match: Match) -> np.ndarray:
        """Return the superclass scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return np.zeros(
                (NUMBER_OF_NPC_SUPERCLASSES,),
            )

        return np.mean(
            [
                lotus.one_hot_encoded_npc_superclass
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def get_npc_class_scores(self, match: Match) -> np.ndarray:
        """Return the class scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return np.zeros(
                (NUMBER_OF_NPC_CLASSES,),
            )

        return np.mean(
            [
                lotus.one_hot_encoded_npc_class
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                * self.cosine_similarity
                for lotus in self.lotus
            ],
            axis=0,
        )

    def lotus_annotations(self) -> List[Lotus]:
        """Return the list of Lotus annotations."""
        return self.lotus
