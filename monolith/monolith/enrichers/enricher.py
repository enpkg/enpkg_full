"""Submodule defining the enricher interface."""

from abc import ABC, abstractmethod
from monolith.data.analysis_class import Analysis


class Enricher(ABC):
    """Interface for enrichers."""

    @abstractmethod
    def enrich(self, analysis: Analysis) -> Analysis:
        """Returns the enriched analysis."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Returns the name of the enricher."""
        pass
