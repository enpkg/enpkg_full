"""Test module to evaluate the current module of the ENPKG workflow."""
from .utils import retrieve_zenodo_data


def test_data_organization():
    """Test whether the data organization is correct."""
    # First, we retrieve the data from Zenodo if we have not done so already.
    # Toy ENPKG dataset is at https://zenodo.org/records/10018590
    retrieve_zenodo_data(record_id="10018590", record_name="enpkg_toy_dataset.zip")