"""Submodule providing the default pipeline for ENPKG analysis."""

from tqdm.auto import tqdm
from monolith.pipeline.pipeline import Pipeline
from monolith.enrichers.enricher import Enricher
from monolith.data.analysis_class import Analysis
from monolith.data.batch_class import Batch
from typing import List, Type
import yaml
from monolith.data import ISDBEnricherConfig

from monolith.enrichers.taxa_enricher import TaxaEnricher
from monolith.enrichers.isdb_enricher import ISDBEnricher


class DefaultPipeline(Pipeline):
    """Default pipeline for ENPKG analysis."""

    def __init__(self, config: str = "config.yaml"):
        """Initializes the pipeline with a list of enrichers."""

        with open(config, "r", encoding="utf-8") as file:
            global_configuration = yaml.safe_load(file)

        isdb_configuration = ISDBEnricherConfig.from_dict(global_configuration["isdb"])

        self.enrichers: List[Type[Enricher]] = [
            # Add enrichers here
            TaxaEnricher(),
            ISDBEnricher(
                isdb_configuration,
                polarity=global_configuration["general"]["polarity"] == "pos",
            ),
        ]

    def process(self, batch: Batch) -> Batch:
        """Processes the batch of analyses."""
        assert isinstance(batch, Batch)

        for enricher in tqdm(
            self.enrichers,
            desc="Processing",
            unit="enricher",
            leave=False,
            dynamic_ncols=True,
        ):
            for analysis in tqdm(
                batch.analyses,
                desc=enricher.name(),
                unit="analysis",
                leave=False,
                dynamic_ncols=True,
            ):
                enricher.enrich(analysis)

        return batch
