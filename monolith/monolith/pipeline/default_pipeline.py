"""Submodule providing the default pipeline for ENPKG analysis."""

from time import time
from typing import Type, Optional
import yaml
from monolith.data import ISDBEnricherConfig, NetworkEnricherConfig, MS1EnricherConfig
from monolith.pipeline.pipeline import Pipeline
from monolith.enrichers.enricher import Enricher
from monolith.enrichers.taxa_enricher import TaxaEnricher
from monolith.enrichers.isdb_enricher import ISDBEnricher
from monolith.enrichers.ms1_enricher import MS1Enricher
from monolith.enrichers.network_enricher import NetworkEnricher
from monolith.exceptions import ConfigurationError


class DefaultPipeline(Pipeline):
    """Default pipeline for ENPKG analysis."""

    enrichers: list[Type[Enricher]]

    def __init__(
        self,
        isdb_configuration: Optional[ISDBEnricherConfig],
        ms1_configuration: Optional[MS1EnricherConfig],
        network_configuration: Optional[NetworkEnricherConfig],
    ):
        """Initializes the pipeline with a list of enrichers."""
        super().__init__()

        if network_configuration is None:
            if ms1_configuration is not None:
                raise ConfigurationError(
                    "When MS1 configuration is provided, "
                    "network configuration must be provided as well."
                )

            if isdb_configuration is not None:
                raise ConfigurationError(
                    "When ISDB configuration is provided, "
                    "network configuration must be provided as well."
                )

        self.enrichers: list[Type[Enricher]] = []

        self.logger.info("Initializing taxa enricher")
        start = time()
        taxa_enricher = TaxaEnricher()
        self.enrichers.append(taxa_enricher)
        self.logger.info("%s took %.2f seconds", taxa_enricher.name(), time() - start)

        if network_configuration is not None:
            self.logger.info("Initializing network enricher")
            start = time()
            network_enricher = NetworkEnricher(network_configuration)
            self.enrichers.append(network_enricher)
            self.logger.info(
                "%s took %.2f seconds", network_enricher.name(), time() - start
            )

        if ms1_configuration is not None:
            self.logger.info("Initializing MS1 enricher")
            start = time()
            ms1_enricher = MS1Enricher(
                ms1_configuration,
                logger=self.logger,
            )
            self.enrichers.append(ms1_enricher)
            self.logger.info("%s took %.2f seconds", ms1_enricher.name(), time() - start)

        if isdb_configuration is not None:
            self.logger.info("Initializing ISDB enricher")
            start = time()
            isdb_enricher = ISDBEnricher(
                isdb_configuration,
                logger=self.logger,
            )
            self.enrichers.append(isdb_enricher)
            self.logger.info("%s took %.2f seconds", taxa_enricher.name(), time() - start)

    @classmethod
    def from_yaml(cls, config: str) -> "DefaultPipeline":
        """Creates a pipeline from a YAML configuration file."""

        with open(config, "r", encoding="utf-8") as file:
            global_configuration = yaml.safe_load(file)

        isdb_configuration = ISDBEnricherConfig.from_dict(global_configuration["isdb"])
        ms1_configuration = MS1EnricherConfig.from_dict(
            global_configuration["ms1_enricher"]
        )
        network_configuration = NetworkEnricherConfig.from_dict(
            global_configuration["network"]
        )

        return cls(
            isdb_configuration=isdb_configuration,
            ms1_configuration=ms1_configuration,
            network_configuration=network_configuration,
        )

    def name(self) -> str:
        """Returns the name of the pipeline."""
        return "Default pipeline"

    def enrichers(self) -> list[Type[Enricher]]:
        """Returns the list of enrichers."""
        return self.enrichers
