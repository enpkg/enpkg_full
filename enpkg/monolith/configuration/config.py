"""
Abstract configuration class for the enrichers.
"""
from abc import ABC

from pydantic import BaseModel, ConfigDict
import yaml

class EnricherConfig(BaseModel, ABC):
    """Interface for building enricher configurations."""

    # Allows using extra fields or forbidden them for strictness
    model_config = ConfigDict(extra='forbid')

    @classmethod
    def from_yaml(cls, path: str):
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        # Use model_validate to leverage Pydantic's parsing logic
        return cls.model_validate(config_dict)
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        return cls.model_validate(config_dict)


