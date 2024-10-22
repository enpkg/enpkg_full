"""Test suite for the default pipeline."""

import logging
from time import time
import compress_json
from monolith.pipeline.default_pipeline import DefaultPipeline
from monolith.data.analysis_class import Analysis
from monolith.data.batch_class import Batch

logging.basicConfig(level=logging.INFO)


class TestDefaultPipeline:
    """Test class to validate performance of the default pipeline."""

    @classmethod
    def compare_time_requirements(cls, test_name: str, elapsed_time: float):
        """Compare the elapsed time with the time requirements."""
        if test_name in cls.time_requirements:
            performance_change = elapsed_time / cls.time_requirements[test_name]
            # If the performance is more than 1%, we consider it statistically significant
            if performance_change > 1.01:
                cls.logger.warning(
                    "Performance WORSENED for '%s': %.2f%%",
                    test_name,
                    performance_change * 100,
                )
            elif performance_change < 0.99:
                cls.logger.info(
                    "Performance IMPROVED for '%s': %.2f%%",
                    test_name,
                    performance_change * 100,
                )
            else:
                cls.logger.info(
                    "No significant performance change for '%s': %.2f%%",
                    test_name,
                    performance_change * 100,
                )
        cls.time_requirements[test_name] = elapsed_time
        compress_json.local_dump(cls.time_requirements, "time_requirements.json")

    @classmethod
    def setup_class(cls):
        """Initialize the pipeline once for the test class."""
        cls.logger = logging.getLogger(__name__)
        cls.logger.setLevel(logging.INFO)

        test_suite_metadata_path = "time_requirements.json"
        try:
            cls.time_requirements = compress_json.local_load(test_suite_metadata_path)
        except FileNotFoundError:
            cls.time_requirements = {}

        start = time()
        cls.pipeline = DefaultPipeline(config="tests/data_for_analysis/config.yaml")
        elapsed_time = time() - start
        cls.compare_time_requirements("Initializing pipeline", elapsed_time)

    def test_default_pipeline_sample(self):
        """Test run for the default pipeline with a sample."""

        start = time()
        batch = Batch(
            metadata_path="tests/data_for_analysis/sample/metadata/metadata.tsv",
            methods_directory="tests/data_for_analysis/sample/methods",
            mzml_directory="tests/data_for_analysis/sample/mzml",
            treated_data_directory="tests/data_for_analysis/sample/treated_data",
        )
        elapsed_time = time() - start
        self.compare_time_requirements("Initializing batch", elapsed_time)

        start = time()
        batch = self.pipeline.process(batch)
        elapsed_time = time() - start
        self.compare_time_requirements("Running pipeline", elapsed_time)

        assert isinstance(batch, Batch)
        assert len(batch.analyses) == 1

        for analysis in batch.analyses:
            assert isinstance(analysis, Analysis)
            assert len(analysis.tandem_mass_spectra) == 678
            assert analysis.number_of_spectra_with_at_least_one_annotation == 191

            # We print the best OTT match for the analysis
            # best_ott_match = analysis.best_ott_match

            for spectrum in analysis.tandem_mass_spectra:
                print(spectrum.get_top_k_lotus_annotation(5))

    # def test_default_pipeline_blank(self):
    #     """Test run for the default pipeline with a blank."""
    #     batch = Batch(
    #         metadata_path="tests/data_for_analysis/blank/metadata/metadata.tsv",
    #         methods_directory="tests/data_for_analysis/blank/methods",
    #         mzml_directory="tests/data_for_analysis/blank/mzml",
    #         treated_data_directory="tests/data_for_analysis/blank/treated_data",
    #     )
    #     batch = self.pipeline.process(batch)
    #     assert isinstance(batch, Batch)
    #     assert len(batch.analyses) == 1

    #     for analysis in batch.analyses:
    #         assert isinstance(analysis, Analysis)
    #         assert len(analysis.tandem_mass_spectra) == 70
    #         assert analysis.number_of_spectra_with_at_least_one_annotation == 24
