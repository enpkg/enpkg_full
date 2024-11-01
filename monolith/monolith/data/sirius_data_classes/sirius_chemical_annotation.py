"""Submodule providing dataclasses for representing chemical annotations from Sirius."""

from dataclasses import dataclass
from monolith.data.lotus_class import Lotus
from monolith.data.chemical_annotation import ChemicalAnnotation
from typing import Optional


@dataclass
class SiriusChemicalAnnotation(ChemicalAnnotation):
    """Dataclass for representing chemical annotations from Sirius."""

    lotus: Optional[list[Lotus]]
    
    def __init__(
        self,
        lotus: Optional[list[Lotus]],
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
            short_inchikey_set: Set[str] = {
                lotus_entry.short_inchikey for lotus_entry in lotus
            }
            assert (
                len(short_inchikey_set) == 1
            ), f"All Lotus entries must have the same Short InChIKey: {short_inchikey_set}."

        self.lotus: Optional[list[Lotus]] = lotus
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks

    def lotus_annotations(self) -> Optional[list[Lotus]]:
        """Return the list of Lotus annotations."""
        return self.lotus
