"""Submodule for creating a similarity network for the analysis."""

import networkx as nx
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

        assert len(ms_network.graph.nodes) == analysis.number_of_spectra, (
            f"The number of nodes in the network ({len(ms_network.graph.nodes)}) "
            f"does not match the number of feature IDs ({analysis.number_of_spectra})"
        )

        # We make sure that the nodes of the graph are sorted by scan number
        corrected_graph = nx.Graph()
        corrected_graph.add_nodes_from(analysis.feature_ids)
        corrected_graph.add_edges_from(ms_network.graph.edges(data=True))

        analysis.set_molecular_network(corrected_graph)

        return analysis
