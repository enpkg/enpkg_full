"""Exceptions used through the monolith package."""


class MonolithError(Exception):
    """Base class for exceptions in the monolith package."""


class PipelineError(MonolithError):
    """Exception raised for errors in the pipeline."""


class ConfigurationError(PipelineError):
    """Exception raised for errors in the configuration."""

class GraphNotSetError(PipelineError):
    """Exception raised when a graph is not set."""

    def __init__(self):
        """Initialize the exception."""
        super().__init__("The graph was not set by the enrichment pipeline")