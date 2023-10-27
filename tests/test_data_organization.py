"""Test module to evaluate the current module of the ENPKG workflow."""
from .utils import retrieve_zenodo_data


def test_data_organization():
    """Test whether the data organization is correct."""
    # First, we retrieve the data from Zenodo if we have not done so already.
    retrieve_zenodo_data(record_id="10043743", record_name="MSV000085119_pos.zip")
    # retrieve_zenodo_data()