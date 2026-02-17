"""
Docstring for enpkg.monolith.pipeline.ms2_enrichment
"""
import logging

from enpkg.monolith.configuration.isdb_configuration_class import ISDBEnricherConfig, Urls, GeneralParams, Paths
from enpkg.monolith.data.analysis import Analysis
from enpkg.monolith.loaders.analysis_loader import AnalysisLoader
from enpkg.monolith.pipeline.base_pipeline_step import PipelineStep
from enpkg.monolith.enrichers.ms2_enricher import Ms2Enricher


class MS2EnrichmentStep(PipelineStep):
    """
    A pipeline step that performs MS2 enrichment.
    """

    def __init__(self, config: ISDBEnricherConfig, logger: logging.Logger):

        super().__init__(config)
        self.logger = logger

    def can_run(self, analysis: Analysis) -> bool:
        # check if analysis has spectra
        return len(analysis.spectra) > 0
    
    def process(self, analysis: Analysis) -> Analysis:
        
        enricher = Ms2Enricher(self.config, self.logger)
        enriched_analysis = enricher.enrich(analysis)
        self.logger.info("MS2 enrichment completed.")
        return enriched_analysis


if __name__ == "__main__":

    analysis = AnalysisLoader.from_files(
        path_to_spectra="/home/llegregam/git_projects/qualone/data/samples/actea_EtOAc-1_pos.mgf",
        path_to_metadata="/home/llegregam/git_projects/qualone/data/metadata/qualome_metadata.txt",
        ionization_mode="pos"
    )
    logger = logging.getLogger("DBLoader")
    logging.basicConfig(level=logging.DEBUG)
    paths = Paths(
        taxo_db_metadata="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_metadata.csv",
        spectral_db_pos="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/spectral_db_pos.pkl",
        taxo_db_pathways="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_pathways.csv",
        taxo_db_superclasses="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_superclasses.csv",
        taxo_db_classes="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_classes.csv"
    )
    urls = Urls(
        taxo_db_metadata="https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz",
        taxo_db_pathways="https://zenodo.org/records/13951644/files/pathways.csv.gz?download=1",
        taxo_db_superclasses="https://zenodo.org/records/13951644/files/superclasses.csv.gz?download=1",
        taxo_db_classes="https://zenodo.org/records/13951644/files/classes.csv.gz?download=1",
        spectral_db_pos="https://zenodo.org/records/8287341/files/isdb_pos_cleaned.pkl"
    )

    config = ISDBEnricherConfig(
        general_params=GeneralParams(
            redownload_if_exists=False
        ),
        urls = urls,
        paths = paths
    )

    step = MS2EnrichmentStep(config, logger)
    step.process(analysis)