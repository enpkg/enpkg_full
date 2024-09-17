"""Submodule providing adducts for all provided Lotus reference chemicals."""

from typing import List
from monolith.data import Lotus
from monolith.data.isdb_data_classes import ChemicalAdduct, AdductRecipe

POSITIVE_RECIPES: List[AdductRecipe] = [
    AdductRecipe(ingredients={"proton": 3}, charge=3, positive=True),
    AdductRecipe(ingredients={"proton": 2, "sodium": 1}, charge=3, positive=True),
    AdductRecipe(ingredients={"proton": 1, "sodium": 2}, charge=3, positive=True),
    AdductRecipe(ingredients={"sodium": 3}, charge=3, positive=True),
    AdductRecipe(ingredients={"proton": 2}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 2, "ammonium": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 1, "sodium": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"magnesium": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 1, "potassium": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"calcium": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 2, "acetonitrile": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"sodium": 2}, charge=2, positive=True),
    AdductRecipe(ingredients={"iron": 1}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 2, "acetonitrile": 2}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 2, "acetonitrile": 3}, charge=2, positive=True),
    AdductRecipe(ingredients={"proton": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "ammonium": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"sodium": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": -1, "magnesium": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "methanol": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"potassium": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": -1, "calcium": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "acetonitrile": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": -1, "sodium": 2}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "ethylamine": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": -1, "iron": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "isopropanol": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"sodium": 1, "acetonitrile": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": -1, "potassium": 2}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "dmso": 1}, charge=1, positive=True),
    AdductRecipe(ingredients={"proton": 1, "acetonitrile": 2}, charge=1, positive=True),
    AdductRecipe(
        ingredients={"magnesium": 1}, charge=2, multimer_factor=2, positive=True
    ),
    AdductRecipe(
        ingredients={"calcium": 1}, charge=2, multimer_factor=2, positive=True
    ),
    AdductRecipe(ingredients={"iron": 1}, charge=2, multimer_factor=2, positive=True),
    AdductRecipe(ingredients={"proton": 1}, charge=1, multimer_factor=2, positive=True),
    AdductRecipe(
        ingredients={"proton": 1, "ammonium": 1},
        charge=1,
        multimer_factor=2,
        positive=True,
    ),
    AdductRecipe(ingredients={"sodium": 1}, charge=1, multimer_factor=2, positive=True),
    AdductRecipe(
        ingredients={"potassium": 1}, charge=1, multimer_factor=2, positive=True
    ),
    AdductRecipe(
        ingredients={"proton": 1, "acetonitrile": 1},
        charge=1,
        multimer_factor=2,
        positive=True,
    ),
    AdductRecipe(
        ingredients={"acetonitrile": 1, "sodium": 1},
        charge=1,
        multimer_factor=2,
        positive=True,
    ),
]

NEGATIVE_RECIPES: List[AdductRecipe] = [
    AdductRecipe(ingredients={"proton": -3}, charge=3, positive=False),
    AdductRecipe(ingredients={"proton": -2}, charge=2, positive=False),
    AdductRecipe(ingredients={"proton": -1}, charge=1, positive=False),
    AdductRecipe(ingredients={"proton": -2, "sodium": 1}, charge=1, positive=False),
    AdductRecipe(ingredients={"chlorine": 1}, charge=1, positive=False),
    AdductRecipe(ingredients={"proton": -2, "potassium": 1}, charge=1, positive=False),
    AdductRecipe(ingredients={"proton": -1, "formic": 1}, charge=1, positive=False),
    AdductRecipe(ingredients={"proton": -1, "acetic": 1}, charge=1, positive=False),
    AdductRecipe(
        ingredients={"proton": -2, "sodium": 1, "formic": 1}, charge=1, positive=False
    ),
    AdductRecipe(ingredients={"bromine": 1}, charge=1, positive=False),
    AdductRecipe(ingredients={"proton": -1, "tfa": 1}, charge=1, positive=False),
    AdductRecipe(
        ingredients={"proton": -1}, charge=1, multimer_factor=2, positive=False
    ),
    AdductRecipe(
        ingredients={"proton": -1, "formic": 1},
        charge=1,
        multimer_factor=2,
        positive=False,
    ),
    AdductRecipe(
        ingredients={"proton": -1, "acetic": 1},
        charge=1,
        multimer_factor=2,
        positive=False,
    ),
    AdductRecipe(
        ingredients={"proton": -1}, charge=1, multimer_factor=3, positive=False
    ),
]


def positive_adducts_from_chemical(lotus: Lotus) -> List[ChemicalAdduct]:
    """Return a list of positive adducts for a given chemical."""
    return [
        ChemicalAdduct(
            lotus=lotus,
            recipe=positive_recipe,
        )
        for positive_recipe in POSITIVE_RECIPES
    ]


def negative_adducts_from_chemical(lotus: Lotus) -> List[ChemicalAdduct]:
    """Return a list of negative adducts for a given chemical."""
    return [
        ChemicalAdduct(
            lotus=lotus,
            recipe=negative_recipe,
        )
        for negative_recipe in NEGATIVE_RECIPES
    ]
