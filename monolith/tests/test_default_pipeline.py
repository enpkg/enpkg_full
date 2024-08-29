"""Test suite for the default pipeline."""

from monolith.pipeline.default_pipeline import DefaultPipeline
from monolith.data.analysis_class import Analysis
from monolith.data.batch_class import Batch

def test_default_pipeline_sample():
    """Test run for the default pipeline with a sample."""
    pipeline = DefaultPipeline(config="tests/data_for_analysis/config.yaml")
    batch = Batch(
        metadata_path="tests/data_for_analysis/sample/metadata/metadata.tsv",
        methods_directory="tests/data_for_analysis/sample/methods",
        mzml_directory="tests/data_for_analysis/sample/mzml",
        treated_data_directory="tests/data_for_analysis/sample/treated_data",
    )
    batch = pipeline.process(batch)
    assert isinstance(batch, Batch)
    assert len(batch.analyses) == 1

def test_default_pipeline_blank():
    """Test run for the default pipeline with a blank."""
    pipeline = DefaultPipeline(config="tests/data_for_analysis/config.yaml")
    batch = Batch(
        metadata_path="tests/data_for_analysis/blank/metadata/metadata.tsv",
        methods_directory="tests/data_for_analysis/blank/methods",
        mzml_directory="tests/data_for_analysis/blank/mzml",
        treated_data_directory="tests/data_for_analysis/blank/treated_data",
    )
    batch = pipeline.process(batch)
    assert isinstance(batch, Batch)
    assert len(batch.analyses) == 1