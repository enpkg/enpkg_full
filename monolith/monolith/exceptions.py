"""Exceptions used through the monolith package."""


class MonolithError(Exception):
    """Base class for exceptions in the monolith package."""


class PipelineError(MonolithError):
    """Exception raised for errors in the pipeline."""


class ConfigurationError(PipelineError):
    """Exception raised for errors in the configuration."""
