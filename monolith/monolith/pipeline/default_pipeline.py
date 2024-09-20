"""Submodule providing the default pipeline for ENPKG analysis."""

from time import time
from typing import List, Type
import yaml
from monolith.data import ISDBEnricherConfig, NetworkEnricherConfig
from monolith.pipeline.pipeline import Pipeline
from monolith.enrichers.enricher import Enricher
from monolith.enrichers.taxa_enricher import TaxaEnricher
from monolith.enrichers.isdb_enricher import ISDBEnricher
from monolith.enrichers.network_enricher import NetworkEnricher


class DefaultPipeline(Pipeline):
    """Default pipeline for ENPKG analysis."""

    enrichers: List[Type[Enricher]]

    def __init__(self, config: str = "config.yaml"):
        """Initializes the pipeline with a list of enrichers."""
        super().__init__()

        with open(config, "r", encoding="utf-8") as file:
            global_configuration = yaml.safe_load(file)

        isdb_configuration = ISDBEnricherConfig.from_dict(global_configuration["isdb"])
        network_configuration = NetworkEnricherConfig.from_dict(
            global_configuration["network"]
        )

        self.logger.info("Initializing taxa enricher")
        start = time()
        taxa_enricher = TaxaEnricher()
        self.logger.info("%s took %.2f seconds", taxa_enricher.name(), time() - start)

        self.logger.info("Initializing network enricher")
        start = time()
        network_enricher = NetworkEnricher(network_configuration)
        self.logger.info(
            "%s took %.2f seconds", network_enricher.name(), time() - start
        )

        self.logger.info("Initializing ISDB enricher")
        start = time()
        isdb_enricher = ISDBEnricher(
            isdb_configuration,
            polarity=global_configuration["general"]["polarity"] == "pos",
            logger=self.logger,
        )
        self.logger.info("%s took %.2f seconds", taxa_enricher.name(), time() - start)

        self.enrichers: List[Type[Enricher]] = [
            taxa_enricher,
            network_enricher,
            isdb_enricher,
        ]

    def name(self) -> str:
        """Returns the name of the pipeline."""
        return "Default pipeline"

    def enrichers(self) -> List[Type[Enricher]]:
        """Returns the list of enrichers."""
        return self.enrichers
