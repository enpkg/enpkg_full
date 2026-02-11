"""
Module defining the molecular networking step in the pipeline.
"""

import pandas as pd
import networkx as nx

from monolith.data.analysis import Analysis
from monolith.pipeline.base_pipeline_step import PipelineStep
from monolith.enrichers.network_enricher import NetworkEnricher
from monolith.configuration.network_enricher_config import NetworkEnricherConfig

class MolecularNetworkingStep(PipelineStep):
    """
    A pipeline step that performs molecular networking.
    """

    def __init__(self, config: NetworkEnricherConfig):

        super().__init__(config)

    def can_run(self, analysis: Analysis) -> bool:
        # check if analysis has spectra
        return len(analysis.spectra) > 0
    
    def export_components(self, analysis: Analysis, path: str) -> None:
        """Export molecular network components to a TSV file.
        
        Components with only one feature are assigned component_id = -1.
        """
        # Get connected components sorted by size (largest first)
        components = sorted(
            nx.connected_components(analysis.molecular_network),
            key=len,
            reverse=True
        )
        
        # Build node-to-component mapping, assigning -1 to singletons
        node_to_component = {}
        for component_id, nodes in enumerate(components, start=1):
            assigned_id = component_id if len(nodes) > 1 else -1
            for node in nodes:
                node_to_component[node] = assigned_id
        
        # Create DataFrame from mapping
        comp_df = pd.DataFrame.from_dict(
            node_to_component, orient="index", columns=["component_id"]
        )
        comp_df.index.name = "feature_id"
        comp_df.reset_index(inplace=True)
        
        # Add precursor_mz from spectra metadata
        spectra_metadata = pd.DataFrame(s.metadata for s in analysis.spectra)
        comp_df = comp_df.merge(
            spectra_metadata[["feature_id", "precursor_mz"]], 
            on="feature_id",
            how="left"
        )
        
        comp_df.to_csv(path, sep="\t", index=False)

    def process(self, analysis: Analysis) -> Analysis:
        
        enricher = NetworkEnricher(configuration=self.config)
        molecular_network = enricher.enrich(analysis)
        return analysis.model_copy(update={"molecular_network": molecular_network})