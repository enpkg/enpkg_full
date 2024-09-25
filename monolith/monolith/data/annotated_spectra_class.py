"""Module to store annotated spectra and MSMS annotations."""

from typing import List, Optional, Dict
from matchms import Spectrum
import numpy as np
from monolith.data.ms1_data_classes import ChemicalAdduct
from monolith.data.isdb_data_classes import ISDBChemicalAnnotation
from monolith.data.sirius_data_classes import SiriusChemicalAnnotation
from monolith.data.lotus_class import (
    Lotus,
    NUMBER_OF_NPC_PATHWAYS,
    NUMBER_OF_NPC_CLASSES,
    NUMBER_OF_NPC_SUPERCLASSES,
)
from monolith.data.otl_class import Match


class AnnotatedSpectrum(Spectrum):
    """Class to store annotated spectra. This is an extension of the matchms Spectrum class"""

    def __init__(
        self,
        spectrum: Spectrum,
        mass_over_charge: float,
        retention_time: float,
        intensity: float,
    ):
        """Initialize the annotated spectrum."""
        super().__init__(
            mz=spectrum.mz,
            intensities=spectrum.intensities,
            metadata=spectrum.metadata,
        )

        # We verify that the provided mass over charge matches
        # the precursor mass over charge
        if abs(mass_over_charge - spectrum.get("precursor_mz")) > 0.001:
            raise ValueError(
                f"Provided mass over charge {mass_over_charge} does not match the precursor mass over charge {spectrum.get('precursor_mz')}"
            )

        self.retention_time: float = retention_time
        self.intensity: float = intensity
        self._sirius_annotations: List[SiriusChemicalAnnotation] = []
        self._isdb_annotations: List[ISDBChemicalAnnotation] = []
        self._ms1_annotations: List[ChemicalAdduct] = []
        self._ms1_npc_pathway_scores: Optional[np.ndarray] = None
        self._ms1_npc_class_scores: Optional[np.ndarray] = None
        self._ms1_npc_superclass_scores: Optional[np.ndarray] = None
        self._isdb_npc_pathway_scores: Optional[np.ndarray] = None
        self._isdb_npc_superclass_scores: Optional[np.ndarray] = None
        self._isdb_npc_class_scores: Optional[np.ndarray] = None

    def set_ms1_npc_pathway_scores(self, npc_pathway_scores: np.ndarray):
        """Set the ms1 propagated NPC pathway annotations"""
        assert isinstance(
            npc_pathway_scores, np.ndarray
        ), "NPC pathway must be a numpy array."
        assert npc_pathway_scores.shape == (
            NUMBER_OF_NPC_PATHWAYS,
        ), "NPC pathway must have the correct shape."
        self._ms1_npc_pathway_scores = npc_pathway_scores

    def set_ms1_npc_superclass_scores(self, npc_superclass_scores: np.ndarray):
        """Set the ms1 propagated NPC superclass annotations"""
        assert isinstance(
            npc_superclass_scores, np.ndarray
        ), "NPC superclass must be a numpy array."
        assert npc_superclass_scores.shape == (
            NUMBER_OF_NPC_SUPERCLASSES,
        ), "NPC superclass must have the correct shape."
        self._ms1_npc_superclass_scores = npc_superclass_scores

    def set_ms1_npc_class_scores(self, npc_class_scores: np.ndarray):
        """Set the ms1 propagated NPC class annotations"""
        assert isinstance(
            npc_class_scores, np.ndarray
        ), "NPC class must be a numpy array."
        assert npc_class_scores.shape == (
            NUMBER_OF_NPC_CLASSES,
        ), "NPC class must have the correct shape."
        self._ms1_npc_class_scores = npc_class_scores

    def set_isdb_npc_pathway_scores(self, npc_pathway_scores: np.ndarray):
        """Set the ISDB propagated NPC pathway annotations"""
        assert isinstance(
            npc_pathway_scores, np.ndarray
        ), "NPC pathway must be a numpy array."
        assert npc_pathway_scores.shape == (
            NUMBER_OF_NPC_PATHWAYS,
        ), "NPC pathway must have the correct shape."
        self._isdb_npc_pathway_scores = npc_pathway_scores

    def set_isdb_npc_superclass_scores(self, npc_superclass_scores: np.ndarray):
        """Set the ISDB propagated NPC superclass annotations"""
        assert isinstance(
            npc_superclass_scores, np.ndarray
        ), "NPC superclass must be a numpy array."
        assert npc_superclass_scores.shape == (
            NUMBER_OF_NPC_SUPERCLASSES,
        ), "NPC superclass must have the correct shape."
        self._isdb_npc_superclass_scores = npc_superclass_scores


    def set_isdb_npc_class_scores(self, npc_class_scores: np.ndarray):
        """Set the ISDB propagated NPC class annotations"""
        assert isinstance(
            npc_class_scores, np.ndarray
        ), "NPC class must be a numpy array."
        assert npc_class_scores.shape == (
            NUMBER_OF_NPC_CLASSES,
        ), "NPC class must have the correct shape."
        self._isdb_npc_class_scores = npc_class_scores

    @property
    def precursor_mz(self):
        """Return the precursor mass over charge"""
        return self.get("precursor_mz")

    @property
    def polarity(self) -> bool:
        """Return the polarity of the spectrum"""
        return self.get("charge") > 0

    @property
    def feature_id(self) -> int:
        """Return the feature ID of the spectrum"""
        return self.get("feature_id")

    @property
    def ms1_annotations(self) -> List[ChemicalAdduct]:
        """Return the possible MS1 adducts"""
        return self._ms1_annotations

    @property
    def isdb_annotations(self) -> List[ISDBChemicalAnnotation]:
        """Return the ISDB annotations"""
        return self._isdb_annotations

    def has_ms1_annotations(self) -> bool:
        """Returns whether the spectrum has MS1 annotations"""
        return len(self._ms1_annotations) > 0

    def set_ms1_annotations(self, adducts: List[ChemicalAdduct]):
        """Set the possible MS1 adducts"""
        self._ms1_annotations = adducts

    def has_isdb_annotations(self) -> bool:
        """Returns whether the spectrum has ISDB annotations"""
        return len(self._isdb_annotations) > 0

    def add_isdb_annotation(self, annotation: ISDBChemicalAnnotation):
        """Add an ISDB annotation to the spectrum."""
        self._isdb_annotations.append(annotation)

    def add_sirius_annotation(self, annotation: SiriusChemicalAnnotation):
        """Add a Sirius annotation to the spectrum."""
        self._sirius_annotations.append(annotation)

    def get_top_k_lotus_annotation(self, k: int = 1) -> Optional[List[Lotus]]:
        """Returns the top k best LOTUS annotation from the MS1 and ISDB MS2 annotations.


        Parameters
        ----------
        k : int
            The number of top LOTUS annotations to return.

        Returns
        -------
        Optional[List[Lotus]]
            The top k best LOTUS annotations.
            If the spectrum has no annotations, returns None.
        """
        if not self.has_isdb_annotations() and not self.has_ms1_annotations():
            return None

        annotations: Dict[Lotus, float] = {}

        for annotation in self._isdb_annotations:
            if annotation.lotus is None:
                continue
            for lotus in annotation.lotus:
                pathway_score = np.mean(
                    [
                        self._isdb_npc_pathway_scores[pathway_id]
                        for pathway_id in lotus.iter_npc_pathways()
                    ]
                )
                superclass_score = np.mean(
                    [
                        self._isdb_npc_superclass_scores[superclass_id]
                        for superclass_id in lotus.iter_npc_superclasses()
                    ]
                )
                class_score = np.mean(
                    [
                        self._isdb_npc_class_scores[class_id]
                        for class_id in lotus.iter_npc_classes()
                    ]
                )

                if pathway_score == 0.0:
                    pathway_score = 1.0
                if superclass_score == 0.0:
                    superclass_score = 1.0
                if class_score == 0.0:
                    class_score = 1.0

                combined_score = pathway_score * superclass_score * class_score
                annotations[lotus] = annotations.get(lotus, 0) + combined_score

        for annotation in self._ms1_annotations:
            for lotus in annotation.lotus:
                pathway_score = np.mean(
                    [
                        self._ms1_npc_pathway_scores[pathway_id]
                        for pathway_id in lotus.iter_npc_pathways()
                    ]
                )
                superclass_score = np.mean(
                    [
                        self._ms1_npc_superclass_scores[superclass_id]
                        for superclass_id in lotus.iter_npc_superclasses()
                    ]
                )
                class_score = np.mean(
                    [
                        self._ms1_npc_class_scores[class_id]
                        for class_id in lotus.iter_npc_classes()
                    ]
                )

                if pathway_score == 0.0:
                    pathway_score = 1.0
                if superclass_score == 0.0:
                    superclass_score = 1.0
                if class_score == 0.0:
                    class_score = 1.0

                combined_score = pathway_score * superclass_score * class_score
                annotations[lotus] = annotations.get(lotus, 0) + combined_score

        return sorted(annotations, key=annotations.get, reverse=True)[:k]

    def best_lotus_annotation_by_ott_match(self, match: Match) -> Optional[Lotus]:
        """Returns the best lotus annotation from the set of MS2 annotations.

        Parameters
        ----------
        match : Match
            The match object containing the best open tree of life match
            given the expected sample taxonomy.

        Implementation details
        -----------------------
        We iterate over the annotations and combine the following scores
        for each annotation:
            - The cosine similarity score (precomputed)
            - The number of matched taxonomical levels between the Lotus entry and the Match entry
            - The chemical reponderation step performs chemical consistency reweighting on the set of MS2 annotations. requires component index.

        We weight the Lotus annotations by these three scores, and return the best one.
        """
        weighted_lotus_entries = [
            (
                annotation.cosine_similarity
                + lotus.taxonomical_similarity_with_otl_match(match),
                lotus,
            )
            for annotation in self._isdb_annotations
            if annotation.lotus is not None
            for lotus in annotation.lotus
        ]

        if not weighted_lotus_entries:
            return None

        return max(weighted_lotus_entries, key=lambda x: x[0])[1]
