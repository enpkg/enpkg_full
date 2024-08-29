from dataclasses import dataclass
from typing import Dict, Any, List
from matchms import Spectrum

@dataclass
class ChemicalAnnotation:
    cosine_similarity: float
    number_of_matched_peaks: int
    molecule_id: int
    short_inchikey: str

    def __init__(self, cosine_similarity: float, number_of_matched_peaks: int, molecule_id: int, short_inchikey: str):
        self.cosine_similarity = cosine_similarity
        self.number_of_matched_peaks = number_of_matched_peaks
        self.molecule_id = molecule_id
        self.short_inchikey = short_inchikey

@dataclass
class AnnotatedSpectra:
    spectrum: Spectrum
    annotations: List[ChemicalAnnotation]

    def __init__(self, spectrum: Spectrum):
        self.spectrum = spectrum
        self.annotations = []

    def add_annotation(self, annotation: ChemicalAnnotation):
        self.annotations.append(annotation)