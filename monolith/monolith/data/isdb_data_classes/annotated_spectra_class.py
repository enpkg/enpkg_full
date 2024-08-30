from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from matchms import Spectrum
from monolith.data.isdb_data_classes.adduct_class import ChemicalAdduct
from monolith.utils import binary_search_by_key

@dataclass
class MS2ChemicalAnnotation:
    cosine_similarity: float
    number_of_matched_peaks: int
    molecule_id: int
    short_inchikey: str

    def __init__(
        self,
        cosine_similarity: float,
        number_of_matched_peaks: int,
        molecule_id: int,
        short_inchikey: str,
    ):
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks
        self.molecule_id = molecule_id
        self.short_inchikey = short_inchikey


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
        self.annotations = []
        self.possible_adducts: List[ChemicalAdduct] = []

    @property
    def precursor_mz(self):
        """Return the precursor mass over charge"""
        return self.spectrum.get("precursor_mz")

    @property
    def polarity(self) -> bool:
        """Return the polarity of the spectrum"""
        return self.spectrum.get("charge") > 0

    def add_annotation(self, annotation: MS2ChemicalAnnotation):
        """Add an ISDB annotation to the spectrum."""
        self.annotations.append(annotation)

    def is_annotated(self):
        """Returns whether the spectrum has at least one annotation."""
        return bool(self.annotations)
    
    def set_filtered_adducts_from_list(
        self,
        adducts: List[ChemicalAdduct],
        tolerance: float
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
        assert not self.possible_adducts, "Possible adducts already set."
        assert isinstance(adducts, list), "Adducts must be a list."
        lower_bound = self.precursor_mz - self.precursor_mz * tolerance
        upper_bound = self.precursor_mz + self.precursor_mz * tolerance
        
        # Find the lower bound by exploring the sorted adducts via binary search
        (_, lower_bound_index) = binary_search_by_key(
            key = lower_bound,
            array= adducts,
            key_func= lambda adduct: adduct.exact_mass,
        )

        # Find the upper bound by linear search starting from the identified lower
        # bound index and iterating up until we wncounter an adduct with an exact mass
        # greater than the upper bound
        upper_bound_index = lower_bound_index

        while upper_bound > adducts[upper_bound_index].exact_mass:
            upper_bound_index += 1
            
            if upper_bound_index == len(adducts):
                break
        
        self.possible_adducts = adducts[lower_bound_index:upper_bound_index]