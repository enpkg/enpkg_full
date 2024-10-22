"""Test to verify that the network enricher works as intended."""

import pytest
from monolith.enrichers import NetworkEnricher
from monolith.data import Batch, Analysis
from monolith.data import NetworkEnricherConfig


def test_network_enricher():
    """Test that the network enricher works as intended."""
    batch = Batch(
        metadata_path="tests/data_for_analysis/sample/metadata/metadata.tsv",
        methods_directory="tests/data_for_analysis/sample/methods",
        mzml_directory="tests/data_for_analysis/sample/mzml",
        treated_data_directory="tests/data_for_analysis/sample/treated_data",
    )

    network_configuration = NetworkEnricherConfig(
        mn_msms_mz_tol=0.01,
        mn_score_cutoff=0.7,
        mn_max_links=10,
        mn_top_n=15,
    )

    network_enricher = NetworkEnricher(network_configuration)

    for analysis in batch.analyses:
        assert isinstance(analysis, Analysis)
        with pytest.raises(RuntimeError):
            _ = analysis.molecular_network

        analysis = network_enricher.enrich(analysis)

        assert isinstance(analysis, Analysis)
        assert analysis.molecular_network is not None
