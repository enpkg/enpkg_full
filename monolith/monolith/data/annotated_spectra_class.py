"""Module to store annotated spectra and MSMS annotations."""

from typing import List, Optional
from matchms import Spectrum
import numpy as np
from monolith.data.isdb_data_classes import ChemicalAdduct, ISDBChemicalAnnotation
from monolith.data.sirius_data_classes import SiriusChemicalAnnotation
from monolith.utils import binary_search_by_key
from monolith.data.lotus_class import (
    Lotus,
    NUMBER_OF_NPC_PATHWAYS,
    NUMBER_OF_NPC_CLASSES,
    NUMBER_OF_NPC_SUPERCLASSES,
)
from monolith.data.otl_class import Match


class AnnotatedSpectra:
    """Class to store annotated spectra."""

    def __init__(
        self,
        spectrum: Spectrum,
        mass_over_charge: float,
        retention_time: float,
        intensity: float,
    ):
        # We verify that the provided mass over charge matches
        # the precursor mass over charge
        if abs(mass_over_charge - spectrum.get("precursor_mz")) > 0.001:
            raise ValueError(
                f"Provided mass over charge {mass_over_charge} does not match the precursor mass over charge {spectrum.get('precursor_mz')}"
            )

        self.spectrum = spectrum
        self.retention_time = retention_time
        self.intensity = intensity
        self.component_id: Optional[int] = None
        self.sirius_annotations: List[SiriusChemicalAnnotation] = []
        self.isdb_annotations: List[ISDBChemicalAnnotation] = []
        self.ms1_possible_adducts: List[ChemicalAdduct] = []
        self.isdb_propagated_npc_pathway: Optional[np.ndarray] = None
        self.isdb_propagated_npc_class: Optional[np.ndarray] = None
        self.isdb_propagated_npc_superclass: Optional[np.ndarray] = None

    def set_isdb_propagated_npc_pathway_annotations(self, npc_pathway: np.ndarray):
        """Set the ISDB propagated NPC pathway annotations"""
        assert isinstance(npc_pathway, np.ndarray), "NPC pathway must be a numpy array."
        assert npc_pathway.shape == (
            NUMBER_OF_NPC_PATHWAYS,
        ), "NPC pathway must have the correct shape."
        self.isdb_propagated_npc_pathway = npc_pathway

    def set_isdb_propagated_npc_superclass_annotations(
        self, npc_superclass: np.ndarray
    ):
        """Set the ISDB propagated NPC superclass annotations"""
        assert isinstance(
            npc_superclass, np.ndarray
        ), "NPC superclass must be a numpy array."
        assert npc_superclass.shape == (
            NUMBER_OF_NPC_SUPERCLASSES,
        ), "NPC superclass must have the correct shape."
        self.isdb_propagated_npc_superclass = npc_superclass

    def set_isdb_propagated_npc_class_annotations(self, npc_class: np.ndarray):
        """Set the ISDB propagated NPC class annotations"""
        assert isinstance(npc_class, np.ndarray), "NPC class must be a numpy array."
        assert npc_class.shape == (
            NUMBER_OF_NPC_CLASSES,
        ), "NPC class must have the correct shape."
        self.isdb_propagated_npc_class = npc_class

    def get_one_hot_encoded_npc_pathway_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC pathway annotations."""
        one_hot = np.zeros(NUMBER_OF_NPC_PATHWAYS)

        for annotation in self.isdb_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_pathway = lotus_entry.npc_pathway
                if npc_pathway is not None and not one_hot[npc_pathway]:
                    print(
                        f"Spectra: {self.feature_id}) ISDB Annotation {lotus_entry.short_inchikey} has pathway {lotus_entry.structure_taxonomy_npclassifier_01pathway}: {one_hot}"
                    )
                    one_hot[npc_pathway] = 1

        for annotation in self.sirius_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_pathway = lotus_entry.npc_pathway
                if npc_pathway is not None:
                    one_hot[npc_pathway] = 1

        for adduct in self.ms1_possible_adducts:
            if adduct.lotus is None:
                continue
            npc_pathway = adduct.lotus.npc_pathway
            if npc_pathway is not None and not one_hot[npc_pathway]:
                print(
                    f"Spectra: {self.feature_id}) Adduct {adduct.lotus.short_inchikey} has pathway {adduct.lotus.structure_taxonomy_npclassifier_01pathway}: {one_hot}"
                )
                one_hot[npc_pathway] = 1

        return one_hot

    def get_one_hot_encoded_npc_class_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC class annotations"""
        one_hot = np.zeros(NUMBER_OF_NPC_CLASSES)

        for annotation in self.isdb_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_class = lotus_entry.npc_class
                if npc_class is not None:
                    one_hot[npc_class] = 1

        for annotation in self.sirius_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_class = lotus_entry.npc_class
                if npc_class is not None:
                    one_hot[npc_class] = 1

        for adduct in self.ms1_possible_adducts:
            if adduct.lotus is None:
                continue
            npc_class = adduct.lotus.npc_class
            if npc_class is not None:
                one_hot[npc_class] = 1

        return one_hot

    def get_one_hot_encoded_npc_superclass_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC superclass annotations"""
        one_hot = np.zeros(NUMBER_OF_NPC_SUPERCLASSES)

        for annotation in self.isdb_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_superclass = lotus_entry.npc_superclass
                if npc_superclass is not None and not one_hot[npc_superclass]:
                    one_hot[npc_superclass] = 1
                    # print(f"Spectra: {self.feature_id}) Adduct {lotus_entry.short_inchikey} has superclass {lotus_entry.structure_taxonomy_npclassifier_02superclass}: {one_hot}")

        for annotation in self.sirius_annotations:
            if annotation.lotus is None:
                continue
            for lotus_entry in annotation.lotus:
                npc_superclass = lotus_entry.npc_superclass
                if npc_superclass is not None:
                    one_hot[npc_superclass] = 1

        for adduct in self.ms1_possible_adducts:
            if adduct.lotus is None:
                continue
            npc_superclass = adduct.lotus.npc_superclass
            if npc_superclass is not None and not one_hot[npc_superclass]:
                one_hot[npc_superclass] = 1
                # print(f"Spectra: {self.feature_id}) Adduct {adduct.lotus.short_inchikey} has superclass {adduct.lotus.structure_taxonomy_npclassifier_02superclass}: {one_hot}")

        return one_hot

    @property
    def precursor_mz(self):
        """Return the precursor mass over charge"""
        return self.spectrum.get("precursor_mz")

    @property
    def polarity(self) -> bool:
        """Return the polarity of the spectrum"""
        return self.spectrum.get("charge") > 0

    @property
    def feature_id(self) -> int:
        """Return the feature ID of the spectrum"""
        return self.spectrum.get("feature_id")

    def add_isdb_annotation(self, annotation: ISDBChemicalAnnotation):
        """Add an ISDB annotation to the spectrum."""
        self.isdb_annotations.append(annotation)

    def add_sirius_annotation(self, annotation: SiriusChemicalAnnotation):
        """Add a Sirius annotation to the spectrum."""
        self.sirius_annotations.append(annotation)

    def is_isdb_annotated(self):
        """Returns whether the spectrum has at least one ISDB annotation."""
        return bool(self.isdb_annotations)

    def set_filtered_adducts_from_list(
        self, adducts: List[ChemicalAdduct], tolerance: float
    ):
        """Add a list of adducts to the spectrum.

        Parameters
        ----------
        adducts : List[ChemicalAdduct]
            List of adducts to filter and add to the spectrum.
            These adducts are assumed sorted by exact mass.
        tolerance : float
            The part per million tolerance to filter the adducts
            by distance from the precursor mass.

        Implementation details
        -----------------------
        Since the adducts are assumed to be sorted by exact mass,
        we can identify the lower bound given the tolerance and
        the precursor mass of the current spectrum. We then iterate
        over the adducts until the exact mass is greater than the
        upper bound. We solely keep these bounds.
        """
        assert not self.ms1_possible_adducts, "Possible adducts already set."
        assert isinstance(adducts, list), "Adducts must be a list."
        lower_bound = self.precursor_mz - self.precursor_mz * tolerance
        upper_bound = self.precursor_mz + self.precursor_mz * tolerance

        # Find the lower bound by exploring the sorted adducts via binary search
        (_, lower_bound_index) = binary_search_by_key(
            key=lower_bound,
            array=adducts,
            key_func=lambda adduct: adduct.adduct_mass,
        )

        # Find the upper bound by linear search starting from the identified lower
        # bound index and iterating up until we wncounter an adduct with an exact mass
        # greater than the upper bound
        upper_bound_index = lower_bound_index

        while upper_bound > adducts[upper_bound_index].adduct_mass:
            upper_bound_index += 1

            if upper_bound_index == len(adducts):
                break

        self.ms1_possible_adducts = adducts[lower_bound_index:upper_bound_index]

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
            for annotation in self.isdb_annotations
            if annotation.lotus is not None
            for lotus in annotation.lotus
        ]

        if not weighted_lotus_entries:
            return None

        return max(weighted_lotus_entries, key=lambda x: x[0])[1]
