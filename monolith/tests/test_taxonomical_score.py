"""Test to evaluate whether the taxonomical score is calculated correctly."""

import pandas as pd
import numpy as np
from monolith.enrichers import TaxaEnricher
from monolith.data import Match, Lotus


def test_taxonomical_score():
    """Test the taxonomical score."""

    enricher: TaxaEnricher = TaxaEnricher()
    species: str = "bombyciferum"
    genus: str = "Verbascum"
    matches: list[Match] = enricher.retrieve_matches(genus, species)

    assert len(matches) > 0, "No matches found for the source taxon"

    best_match: Match = matches[0]

    assert best_match.genus == genus, "The genus of the match is not the expected one"
    assert (
        best_match.species == f"{genus} {species}"
    ), "The species of the match is not the expected one"

    lotus_df: pd.DataFrame = pd.read_csv("db_metadata/230106_frozen_metadata.csv")

    Lotus.setup_lotus_columns(lotus_df.columns)

    pathways = np.zeros(7)
    superclasses = np.zeros(70)
    classes = np.zeros(700)

    lotus_entries: list[Lotus] = [
        Lotus.from_pandas_series(
            row, pathways=pathways, superclasses=superclasses, classes=classes
        )
        for row in lotus_df.values
    ]

    lotus_entries_with_scores: list[tuple[Lotus, float]] = [
        (entry, entry.normalized_taxonomical_similarity_with_otl_match(best_match))
        for entry in lotus_entries
    ]

    lotus_entries_with_scores = sorted(
        lotus_entries_with_scores, key=lambda x: x[1], reverse=True
    )

    print(lotus_entries_with_scores[:10])
