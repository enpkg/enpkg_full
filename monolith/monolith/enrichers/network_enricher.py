"""Submodule for creating a similarity network for the analysis."""

from matchms import calculate_scores
from matchms.similarity import ModifiedCosine
from matchms.networking import SimilarityNetwork
from monolith.enrichers.enricher import Enricher
from monolith.data import Analysis
from monolith.data import NetworkEnricherConfig


class NetworkEnricher(Enricher):
    """Enricher that creates a Spectral Network from spectra of the analysis."""

    def __init__(self, configuration: NetworkEnricherConfig):
        """Initializes the enricher."""
        assert isinstance(configuration, NetworkEnricherConfig)

        self.configuration = configuration

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "Network Enricher"

    def enrich(self, analysis: Analysis) -> Analysis:
        """Adds ISDB information to the analysis."""

        similarities = calculate_scores(
            analysis.tandem_mass_spectra,
            analysis.tandem_mass_spectra,
            similarity_function=ModifiedCosine(
                tolerance=self.configuration.mn_msms_mz_tol
            ),
            is_symmetric=True,
        )

        ms_network = SimilarityNetwork(
            identifier_key="scans",
            score_cutoff=self.configuration.mn_score_cutoff,
            top_n=self.configuration.mn_top_n,
            max_links=self.configuration.mn_max_links,
            link_method="mutual",
        )
        ms_network.create_network(similarities, score_name="ModifiedCosine_score")

        analysis.set_molecular_network(ms_network.graph)

        return analysis
