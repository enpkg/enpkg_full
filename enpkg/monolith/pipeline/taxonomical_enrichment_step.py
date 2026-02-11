"""
A pipeline step that performs taxonomical enrichment from a source taxon using the Open Tree of Life API.
"""

from monolith.data.analysis import Analysis
from monolith.pipeline.base_pipeline_step import PipelineStep
from monolith.enrichers.taxa_enricher import TaxaEnricher

class TaxonomicalEnrichmentStep(PipelineStep):

    def process(self, analysis: Analysis) -> Analysis:
        # 1. Guard check
        if not analysis.has_source_taxon:
            self.logger.info("Source taxon not defined, skipping.")
            return analysis
        
        # 2. Call the worker
        genus, species = analysis.genus_and_species
        enricher = TaxaEnricher()
        new_matches = enricher.enrich(genus, species)

        # 3. Perform update
        return analysis.model_copy(
            update={"ott_matches": analysis.ott_matches + new_matches}
        )
    
    def can_run(self, analysis: Analysis) -> bool:
        """
        Check if the source taxon is defined for this analysis and thus if the step can run.
        """
        return analysis.has_source_taxon