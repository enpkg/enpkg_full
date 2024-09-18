"""Submodule providing the data class for representing chemical adducts.

A chemical adducts is a molecules form by the combination of the analyte and a given ions. For example [M+H]+ is the adduct formed by the analyte and a proton. This data class is used to represent the adducts in the MS1 annotation process.
"""

from typing import Dict
from dataclasses import dataclass
from monolith.data.lotus_class import Lotus

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
    inchikey: str, the InChIKey of the molecule. For example BSYNRYMUTXBXSQ-UHFFFAOYSA-N
    exact_mass: float, the exact mass of the molecule . For example 180.0423 g/mol
    adduct_type: str, the type of adduct. For example [M+H]+
    adduct_mass: float, the exact mass of the adduct. For example 181.0495 g/mol
    polarity: str, the polarity of the adduct. For example positive
    charge: int, the charge of the adduct. For example 1
    """

    lotus: Lotus
    recipe: AdductRecipe
    adduct_mass: float

    def __init__(self, lotus: Lotus, recipe: AdductRecipe):
        self.lotus = lotus
        self.recipe = recipe
        self.adduct_mass = recipe.compute_adduct_mass(lotus.structure_exact_mass)

    @property
    def short_inchikey(self) -> str:
        """Return the first 14 characters of the inchikey."""
        return self.lotus.short_inchikey

    @property
    def positive(self) -> bool:
        """Return whether the adduct is positive or negative."""
        return self.recipe.positive
