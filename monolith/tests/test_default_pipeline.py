"""Test suite for the default pipeline."""


import logging

logging.basicConfig(level=logging.INFO)


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
            assert analysis.number_of_spectra_with_at_least_one_annotation == 10 #191

            # We print the best OTT match for the analysis
            best_ott_match = analysis.best_ott_match

            print(best_ott_match)

            best_lotus_per_spectrum = list(analysis.best_lotus_annotation_per_spectra)

            print(best_lotus_per_spectrum)

            # We print the best OTT match for the analysis
            best_ott_match = analysis.best_ott_match

            print(best_ott_match)

            assert len(best_lotus_per_spectrum) == 3 #178

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
            assert analysis.number_of_spectra_with_at_least_one_annotation == 1 #24
