"""
Interface for a pipeline step.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from enpkg.monolith.data.analysis import Analysis


class PipelineStep(ABC):
    """
    Interface for a pipeline step.
    """

    def __init__(self, config: BaseModel = None):
        self.config = config


    def name(self) -> str:
        """Return the name of the pipeline step."""
        return self.__class__.__name__
    
    @abstractmethod
    def process(self, analysis: Analysis) -> Analysis:
        pass
    
    @abstractmethod
    def can_run(self, analysis: Analysis) -> bool:
        """Check if the step can run on the given analysis."""
        pass
