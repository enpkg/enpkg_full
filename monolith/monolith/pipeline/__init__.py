"""Submodule providing the pipelines and the pipeline interface."""

from monolith.pipeline.pipeline import Pipeline
from monolith.pipeline.default_pipeline import DefaultPipeline

__all__ = ["Pipeline", "DefaultPipeline"]
