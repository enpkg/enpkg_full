"""Module to store annotated spectra and MSMS annotations."""

from typing import Optional, Dict, Any, Tuple
from matchms import Spectrum
import numpy as np
from scipy.stats import entropy
from monolith.data.ms1_data_classes import ChemicalAdduct
from monolith.data.isdb_data_classes import ISDBChemicalAnnotation
from monolith.data.sirius_data_classes import SiriusChemicalAnnotation
from monolith.data.lotus_class import (
    Lotus,
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
                f"Provided mass over charge {mass_over_charge} does "
                f"not match the precursor mass over charge {spectrum.get('precursor_mz')}"
            )

        self.retention_time: float = retention_time
        self.intensity: float = intensity
        self._sirius_annotations: list[SiriusChemicalAnnotation] = []
        self._isdb_annotations: list[ISDBChemicalAnnotation] = []
        self._ms1_annotations: list[ChemicalAdduct] = []
        self._ms1_hammer_pathway_scores: Optional[np.ndarray] = None
        self._ms1_hammer_class_scores: Optional[np.ndarray] = None
        self._ms1_hammer_superclass_scores: Optional[np.ndarray] = None
        self._isdb_hammer_pathway_scores: Optional[np.ndarray] = None
        self._isdb_hammer_superclass_scores: Optional[np.ndarray] = None
        self._isdb_hammer_class_scores: Optional[np.ndarray] = None

    def set_ms1_hammer_pathway_scores(self, npc_pathway_scores: np.ndarray):
        """Set the ms1 propagated NPC pathway annotations"""
        self._ms1_hammer_pathway_scores = npc_pathway_scores

    def set_ms1_hammer_superclass_scores(self, npc_superclass_scores: np.ndarray):
        """Set the ms1 propagated NPC superclass annotations"""
        self._ms1_hammer_superclass_scores = npc_superclass_scores

    def set_ms1_hammer_class_scores(self, npc_class_scores: np.ndarray):
        """Set the ms1 propagated NPC class annotations"""
        self._ms1_hammer_class_scores = npc_class_scores

    def set_isdb_hammer_pathway_scores(self, npc_pathway_scores: np.ndarray):
        """Set the ISDB propagated NPC pathway annotations"""
        self._isdb_hammer_pathway_scores = npc_pathway_scores

    def set_isdb_hammer_superclass_scores(self, npc_superclass_scores: np.ndarray):
        """Set the ISDB propagated NPC superclass annotations"""
        self._isdb_hammer_superclass_scores = npc_superclass_scores

    def set_isdb_hammer_class_scores(self, npc_class_scores: np.ndarray):
        """Set the ISDB propagated NPC class annotations"""
        self._isdb_hammer_class_scores = npc_class_scores

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
    def ms1_annotations(self) -> list[ChemicalAdduct]:
        """Return the possible MS1 adducts"""
        return self._ms1_annotations

    @property
    def isdb_annotations(self) -> list[ISDBChemicalAnnotation]:
        """Return the ISDB annotations"""
        return self._isdb_annotations

    def has_ms1_annotations(self) -> bool:
        """Returns whether the spectrum has MS1 annotations"""
        return len(self._ms1_annotations) > 0

    def set_ms1_annotations(self, adducts: list[ChemicalAdduct]):
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

    def get_top_k_lotus_annotation(self, k: int = 1) -> Optional[list[Lotus]]:
        """Returns the top k best LOTUS annotation from the MS1 and ISDB MS2 annotations.


        Parameters
        ----------
        k : int
            The number of top LOTUS annotations to return.

        Returns
        -------
        Optional[list[Lotus]]
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
                    lotus.structure_taxonomy_hammer_pathways.values
                    * self._isdb_hammer_pathway_scores
                )
                superclass_score = np.mean(
                    lotus.structure_taxonomy_hammer_superclasses.values
                    * self._isdb_hammer_superclass_scores
                )
                class_score = np.mean(
                    lotus.structure_taxonomy_hammer_classes.values
                    * self._isdb_hammer_class_scores
                )

                combined_score = pathway_score * superclass_score * class_score
                annotations[lotus] = annotations.get(lotus, 0) + combined_score

        for annotation in self._ms1_annotations:
            for lotus in annotation.lotus:
                pathway_score = np.mean(
                    lotus.structure_taxonomy_hammer_pathways.values
                    * self._ms1_hammer_pathway_scores
                )
                superclass_score = np.mean(
                    lotus.structure_taxonomy_hammer_superclasses.values
                    * self._ms1_hammer_superclass_scores
                )
                class_score = np.mean(
                    lotus.structure_taxonomy_hammer_classes.values
                    * self._ms1_hammer_class_scores
                )

                combined_score: float = pathway_score * superclass_score * class_score
                annotations[lotus] = annotations.get(lotus, 0) + combined_score

        return sorted(annotations, key=annotations.get, reverse=True)[:k]

    def best_chemical_annotation(
        self,
        match: Optional[Match],
        ms1_importance_score: float = 0.5,
        isdb_importance_score: float = 0.5,
    ) -> Optional[Tuple[Lotus, float, str]]:
        """Returns the best Chemical Annotation from the set of MS2 annotations.

        Parameters
        ----------
        match : Optional[Match]
            The match object containing the best open tree of life match
            given the expected sample taxonomy. In some cases, spectra may
            come from unknown sources that  prevent us to retrieve the OTL match.
            In such cases, we ignore the taxonomical reponderation step.
        """
        assert ms1_importance_score + isdb_importance_score == 1

        if not self.has_isdb_annotations() and not self.has_ms1_annotations():
            return None

        pathway_scores = np.zeros_like(self._isdb_hammer_pathway_scores)
        superclass_scores = np.zeros_like(self._isdb_hammer_superclass_scores)
        class_scores = np.zeros_like(self._isdb_hammer_class_scores)

        if self._isdb_hammer_pathway_scores.sum() > 0:
            assert self._isdb_hammer_superclass_scores.sum() > 0
            assert self._isdb_hammer_class_scores.sum() > 0
            pathway_scores += isdb_importance_score * self._isdb_hammer_pathway_scores
            superclass_scores += (
                isdb_importance_score * self._isdb_hammer_superclass_scores
            )
            class_scores += isdb_importance_score * self._isdb_hammer_class_scores
        else:
            isdb_importance_score = 0

        if self._ms1_hammer_pathway_scores.sum() > 0:
            assert self._ms1_hammer_superclass_scores.sum() > 0
            assert self._ms1_hammer_class_scores.sum() > 0
            pathway_scores += ms1_importance_score * self._ms1_hammer_pathway_scores
            superclass_scores += (
                ms1_importance_score * self._ms1_hammer_superclass_scores
            )
            class_scores += ms1_importance_score * self._ms1_hammer_class_scores
        else:
            ms1_importance_score = 0

        # We adjust the scores in case one of the two scores is zero
        pathway_scores /= isdb_importance_score + ms1_importance_score
        superclass_scores /= isdb_importance_score + ms1_importance_score
        class_scores /= isdb_importance_score + ms1_importance_score

        isdb_annotations: list[Tuple[ISDBChemicalAnnotation, Lotus, float]] = []

        for annotation in self._isdb_annotations:
            if not annotation.has_lotus_annotations():
                continue
            # # Next, we store the KL divergence score for the pathways scores
            entropy_score: float = (
                entropy(
                    annotation.get_hammer_pathway_scores(),
                    pathway_scores,
                )
                * entropy(
                    annotation.get_hammer_superclass_scores(),
                    superclass_scores,
                )
                * entropy(
                    annotation.get_hammer_class_scores(),
                    class_scores,
                )
            )
            entropy_score=1.0
            for lotus_annotation in annotation.lotus_annotations():
                # Next, we store the taxonomical reponderation score
                if match is not None:
                    taxonomical_similarity: float = (
                        lotus_annotation.normalized_taxonomical_similarity_with_otl_match(
                            match
                        )
                    )
                else:
                    taxonomical_similarity: float = 0.0

                isdb_annotations.append(
                    (
                        annotation,
                        lotus_annotation,
                        taxonomical_similarity / entropy_score,
                    )
                )

        ms1_annotations: list[Tuple[Lotus, float]] = []

        for annotation in self._ms1_annotations:
            # Next, we store the KL divergence score for the pathways scores
            entropy_score: float = (
                entropy(
                    annotation.get_hammer_pathway_scores(),
                    pathway_scores,
                )
                * entropy(
                    annotation.get_hammer_superclass_scores(),
                    superclass_scores,
                )
                * entropy(
                    annotation.get_hammer_class_scores(),
                    class_scores,
                )
            )
            entropy_score=1.0
            for lotus_annotation in annotation.lotus:
                # Next, we store the taxonomical reponderation score
                if match is not None:
                    taxonomical_similarity: float = (
                        lotus_annotation.normalized_taxonomical_similarity_with_otl_match(
                            match
                        )
                    )
                else:
                    taxonomical_similarity: float = 0.0

                ms1_annotations.append(
                    (
                        lotus_annotation,
                        taxonomical_similarity / entropy_score,
                    )
                )

        # We rank first the isdb annotations, which include in their sorting
        # procedure also the cosine similarity. After that, we strictly compare
        # the MS1 annotations with the ISDB annotations using the combination of
        # taxonomical similarity and entropy.

        if len(isdb_annotations) > 0:
            most_similar_isdb_annotation: Tuple[
                ISDBChemicalAnnotation, Lotus, float
            ] = max(isdb_annotations, key=lambda x: x[2] * x[0].cosine_similarity)
            most_similar_isdb_annotation: Tuple[Optional[Lotus], float] = (
                most_similar_isdb_annotation[1],
                most_similar_isdb_annotation[2],
            )
        else:
            most_similar_isdb_annotation: Tuple[Optional[Lotus], float] = (
                None,
                -np.inf,
            )

        if len(ms1_annotations) > 0:
            most_similar_ms1_annotation: Tuple[Optional[Lotus], float] = max(
                ms1_annotations, key=lambda x: x[1]
            )
        else:
            most_similar_ms1_annotation: Tuple[Optional[Lotus], float] = (None, -np.inf)

        if most_similar_isdb_annotation[1] > most_similar_ms1_annotation[1]:
            return most_similar_isdb_annotation[0], most_similar_isdb_annotation[1], "ISDB"
        return most_similar_ms1_annotation[0], most_similar_ms1_annotation[1], "MS1"

    def into_dict(self, match: Optional[Match]) -> Dict[str, Any]:
        """Returns the main features of the spectrum as a dictionary."""
        annotation_candidate: Optional[Tuple[Lotus, float]] = (
            self.best_chemical_annotation(match)
        )

        annotation_metadata = {}
        if annotation_candidate is not None:
            annotation, score, label = annotation_candidate
            annotation_metadata = annotation.to_dict()
            annotation_metadata["annotation_score"] = score
            annotation_metadata["source"] = label

        return {
            "feature_id": self.feature_id,
            **annotation_metadata,
        }
