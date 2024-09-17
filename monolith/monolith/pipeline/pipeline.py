"""An abstract interface for pipelines to process a batch of analyses."""

from abc import ABC, abstractmethod
from typing import List, Type
from time import time
from logging import Logger, getLogger
from tqdm.auto import tqdm
from monolith.data.batch_class import Batch
from monolith.enrichers.enricher import Enricher


class Pipeline(ABC):
    """Interface for pipelines."""
    
    logger: Logger

    def __init__(self):
        """Initializes the pipeline."""
        self.logger = getLogger(self.name())
        self.logger.info("Initializing pipeline %s", self.name())

    @abstractmethod
    def name(self) -> str:
        """Returns the name of the pipeline."""

    @abstractmethod
    def enrichers(self) -> List[Type[Enricher]]:
        """Returns the list of enrichers."""

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
            start = time()
            for analysis in tqdm(
                batch.analyses,
                desc=enricher.name(),
                unit="analysis",
                leave=False,
                dynamic_ncols=True,
            ):
                enricher.enrich(analysis)
            total_time = time() - start
            average_time_per_analysis = total_time / len(batch.analyses)
            self.logger.info("%s took %.2f seconds", enricher.name(), total_time)
            self.logger.info(
                "Average time per analysis: %.2f seconds", average_time_per_analysis
            )

        return batch
