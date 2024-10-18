"""MS1 Enricher configuration class."""

from dataclasses import dataclass
from typing import Dict, Any
from typeguard import typechecked


@dataclass
class MS1EnricherConfig:
    """Configuration for MS1 Enricher."""

    taxo_db_metadata_path: str
    taxo_db_metadata_url: str
    taxo_db_pathways_url: str
    taxo_db_pathways_path: str
    taxo_db_superclasses_url: str
    taxo_db_superclasses_path: str
    taxo_db_classes_url: str
    taxo_db_classes_path: str
    tolerance: float

    @classmethod
    @typechecked
    def from_dict(cls, data: Dict[str, Any]) -> "MS1EnricherConfig":
        """Creates an instance from a dictionary."""
        return cls(
            taxo_db_metadata_path=data["taxo_db_metadata_path"],
            taxo_db_metadata_url=data["taxo_db_metadata_url"],
            taxo_db_pathways_url=data["taxo_db_pathways_url"],
            taxo_db_pathways_path=data["taxo_db_pathways_path"],
            taxo_db_superclasses_url=data["taxo_db_superclasses_url"],
            taxo_db_superclasses_path=data["taxo_db_superclasses_path"],
            taxo_db_classes_url=data["taxo_db_classes_url"],
            taxo_db_classes_path=data["taxo_db_classes_path"],
            tolerance=data["tolerance_ppm"] / 1e6,
        )
