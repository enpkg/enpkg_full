"""Test suite for the default pipeline."""

import pytest
from monolith.pipeline.default_pipeline import DefaultPipeline
from monolith.data.analysis_class import Analysis
from monolith.data.batch_class import Batch

class TestDefaultPipeline:
    @classmethod
    def setup_class(cls):
        """Initialize the pipeline once for the test class."""
        cls.pipeline = DefaultPipeline(config="tests/data_for_analysis/config.yaml")

    def test_default_pipeline_sample(self):
        """Test run for the default pipeline with a sample."""
        batch = Batch(
            metadata_path="tests/data_for_analysis/sample/metadata/metadata.tsv",
            methods_directory="tests/data_for_analysis/sample/methods",
            mzml_directory="tests/data_for_analysis/sample/mzml",
            treated_data_directory="tests/data_for_analysis/sample/treated_data",
        )
        batch = self.pipeline.process(batch)
        assert isinstance(batch, Batch)
        assert len(batch.analyses) == 1

        for analysis in batch.analyses:
            assert isinstance(analysis, Analysis)
            assert len(analysis.annotated_tandem_mass_spectra) == 678
            assert analysis.number_of_spectra_with_at_least_one_annotation == 191

    def test_default_pipeline_blank(self):
        """Test run for the default pipeline with a blank."""
        batch = Batch(
            metadata_path="tests/data_for_analysis/blank/metadata/metadata.tsv",
            methods_directory="tests/data_for_analysis/blank/methods",
            mzml_directory="tests/data_for_analysis/blank/mzml",
            treated_data_directory="tests/data_for_analysis/blank/treated_data",
        )
        batch = self.pipeline.process(batch)
        assert isinstance(batch, Batch)
        assert len(batch.analyses) == 1

        for analysis in batch.analyses:
            assert isinstance(analysis, Analysis)
            assert len(analysis.annotated_tandem_mass_spectra) == 70
            assert analysis.number_of_spectra_with_at_least_one_annotation == 24