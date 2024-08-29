"""Test submodule to test the batch dataclass."""

from monolith.data import Batch, Analysis


def test_batch_sample():
    """Test the batch dataclass for samples."""
    batch = Batch(
        metadata_path="tests/data_for_analysis/sample/metadata/metadata.tsv",
        methods_directory="tests/data_for_analysis/sample/methods",
        mzml_directory="tests/data_for_analysis/sample/mzml",
        treated_data_directory="tests/data_for_analysis/sample/treated_data",
    )
    assert batch.number_of_analyses == 1

def test_batch_blank():
    """Test the batch dataclass for blank samples."""
    batch = Batch(
        metadata_path="tests/data_for_analysis/blank/metadata/metadata.tsv",
        methods_directory="tests/data_for_analysis/blank/methods",
        mzml_directory="tests/data_for_analysis/blank/mzml",
        treated_data_directory="tests/data_for_analysis/blank/treated_data",
    )
    assert batch.number_of_analyses == 1