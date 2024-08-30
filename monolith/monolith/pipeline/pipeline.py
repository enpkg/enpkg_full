"""An abstract interface for pipelines to process a batch of analyses."""

from abc import ABC, abstractmethod
from monolith.data.batch_class import Batch


class Pipeline(ABC):
    """Interface for pipelines."""

    @abstractmethod
    def process(self, batch: Batch) -> Batch:
        """Returns the processed batch."""
        pass
