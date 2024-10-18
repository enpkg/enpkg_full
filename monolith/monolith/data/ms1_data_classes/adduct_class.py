"""Submodule providing the data class for representing chemical adducts."""

from typing import Dict, List
from dataclasses import dataclass
import numpy as np
from typeguard import typechecked
from monolith.data.lotus_class import Lotus
from monolith.data.otl_class import Match

ADDUCT_MASSES: Dict[str, float] = {
    "proton": 1.00728,
    "ammonium": 17.02655,
    "water": 18.01056,
    "sodium": 22.98977,
    "magnesium": 23.98504,
    "methanol": 32.02621,
    "chlorine": 34.96885,
    "potassium": 38.96371,
    "calcium": 39.96259,
    "acetonitrile": 41.02655,
    "ethylamine": 45.05785,
    "formic": 46.00548,
    "iron": 55.93494,
    "acetic": 60.02113,
    "isopropanol": 60.05751,
    "dmso": 78.01394,
    "bromine": 78.91834,
    "tfa": 113.99286,
}


@dataclass
class AdductRecipe:
    """Dataclass representing an adduct recipe.

    Attributes:
        ingredients: Dict[str, int] - A dictionary of adducts and their counts.
        charge: int - The charge of the adduct.
        multimer_factor: int - The factor by which the adduct mass should be multiplied.
        positive: bool - Whether the adduct is positive or negative.
    """

    ingredients: Dict[str, float]
    charge: float
    positive: bool
    multimer_factor: float = 1.0

    @typechecked
    def compute_adduct_mass(self, exact_lotus_mass: float) -> float:
        """Applies the adduct recepy to the provided exact lotus mass"""
        return (
            self.multimer_factor * exact_lotus_mass
            + sum(ADDUCT_MASSES[key] * count for key, count in self.ingredients.items())
        ) / self.charge


class ChemicalAdduct:
    """Data class representing a chemical adduct.

    Attributes:
    -----------
    lotus: List[Lotus]
        A list of Lotus entries that are part of the adduct.
        All Lotus entries must have the same exact mass and chemical formula.
    recipe: AdductRecipe
        The recipe used to create the adduct.
    adduct_mass: float
        The mass of the adduct determined using the recipe and the exact mass of the Lotus entries.
    """

    lotus: List[Lotus]
    recipe: AdductRecipe
    adduct_mass: float

    @typechecked
    def __init__(self, lotus: List[Lotus], recipe: AdductRecipe):
        assert len(lotus) > 0, "The lotus must not be empty"

        # All lotus entries must have the same exact mass and chemical formula
        structure_exact_mass = lotus[0].structure_exact_mass
        structure_molecular_formula = lotus[0].structure_molecular_formula
        for lotus_entry in lotus[1:]:
            assert (
                lotus_entry.structure_molecular_formula == structure_molecular_formula
            ), (
                f"All lotus entries must have the same molecular formula, "
                f"but got {lotus_entry.structure_molecular_formula} and {structure_molecular_formula}"
            )

        self.lotus = lotus
        self.recipe = recipe
        self.adduct_mass = recipe.compute_adduct_mass(structure_exact_mass)

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the inchikey."""
        return self.lotus[0].short_inchikey

    @property
    def molecular_formula(self) -> str:
        """Return the molecular formula of the adduct."""
        return self.lotus[0].structure_molecular_formula

    @property
    def positive(self) -> bool:
        """Return whether the adduct is positive or negative."""
        return self.recipe.positive

    @typechecked
    def get_hammer_pathway_scores(self, match: Match) -> np.ndarray:
        """Return the pathway scores for the adduct."""
        return np.mean(
            [
                lotus.structure_taxonomy_hammer_pathways.values
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                for lotus in self.lotus
            ],
            axis=0,
        )

    @typechecked
    def get_hammer_superclass_scores(self, match: Match) -> np.ndarray:
        """Return the superclass scores for the adduct."""
        return np.mean(
            [
                lotus.structure_taxonomy_hammer_superclasses.values
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                for lotus in self.lotus
            ],
            axis=0,
        )

    @typechecked
    def get_hammer_class_scores(self, match: Match) -> np.ndarray:
        """Return the class scores for the adduct."""
        return np.mean(
            [
                lotus.structure_taxonomy_hammer_classes.values
                * lotus.normalized_taxonomical_similarity_with_otl_match(match)
                for lotus in self.lotus
            ],
            axis=0,
        )
