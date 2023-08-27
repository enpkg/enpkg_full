"""Test module to evaluate whether the current module of the ENPKG workflow."""
from .utils import retrieve_zenodo_data


def test_enpkg_graph_builder():
    """Test whether the data organization is correct."""
    # First, we retrieve the data from Zenodo if we have not done so already.
    retrieve_zenodo_data()
