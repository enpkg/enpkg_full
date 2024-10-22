"""Submodule providing dataclasses for representing MS2-level chemical annotations from ISDB."""

from typing import List, Optional, Set
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

        # The Lotus entries may be associated to different taxonomical entries
        # but they must have the same chemical structure, therefore the InChIKey
        # of the Lotus entries should be the same.
        if lotus is not None:
            assert len(lotus) > 0, "The list of Lotus entries must not be empty."
            short_inchikey_set: Set[str] = {lotus_entry.short_inchikey for lotus_entry in lotus}
            assert len(short_inchikey_set) == 1, f"All Lotus entries must have the same Short InChIKey: {short_inchikey_set}."

        self.lotus: Optional[List[Lotus]] = lotus
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks

    def has_lotus_entries(self) -> bool:
        """Return whether the annotation has Lotus entries."""
        return self.lotus is not None

    @typechecked
    def maximal_normalized_taxonomical_similarity(
        self, match: Match
    ) -> Optional[float]:
        """Return the maximal normalized taxonomical similarity of the adduct."""
        if self.lotus is None:
            return None

        return max(
            lotus.normalized_taxonomical_similarity_with_otl_match(match)
            for lotus in self.lotus
        )

    @typechecked
    def get_hammer_pathway_scores(self) -> Optional[np.ndarray]:
        """Return the pathway scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        # All of the pathway scores are associated to the same InChIKey, so we can
        # just return the pathway scores of the first Lotus entry as they must all
        # be the same.
        return self.lotus[0].structure_taxonomy_hammer_pathways.values

    def get_hammer_superclass_scores(self) -> Optional[np.ndarray]:
        """Return the superclass scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        # All of the superclass scores are associated to the same InChIKey, so we can
        # just return the superclass scores of the first Lotus entry as they must all
        # be the same.
        return self.lotus[0].structure_taxonomy_hammer_superclasses.values

    def get_hammer_class_scores(self) -> Optional[np.ndarray]:
        """Return the class scores for the ISDB chemical annotation."""
        if self.lotus is None:
            return None

        # All of the class scores are associated to the same InChIKey, so we can
        # just return the class scores of the first Lotus entry as they must all
        # be the same.
        return self.lotus[0].structure_taxonomy_hammer_classes.values

    def lotus_annotations(self) -> Optional[List[Lotus]]:
        """Return the list of Lotus annotations."""
        return self.lotus
