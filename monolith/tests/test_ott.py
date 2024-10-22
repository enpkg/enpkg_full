"""Submodule of the test suite to check that OTL works as intended."""

from typing import Dict
from opentree import OT


def test_otl():
    """Test that OTL works as intended."""

    genus: str = "Verbascum"
    species: str = "bombyciferum"

    ott_match: Dict = OT.tnrs_match(
        [f"{genus} {species}"],
        context_name=None,
        do_approximate_matching=True,
        include_suppressed=False,
    ).response_dict

    assert "results" in ott_match, "No results in the OTT match"


