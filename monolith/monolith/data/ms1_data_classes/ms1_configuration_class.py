"""MS1 Enricher configuration class."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MS1EnricherConfig:
    """Configuration for MS1 Enricher."""

    taxo_db_metadata_path: str
    taxo_db_metadata_url: str
    tolerance: float

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MS1EnricherConfig":
        """Creates an instance from a dictionary."""
        return MS1EnricherConfig(
            taxo_db_metadata_path=data["taxo_db_metadata_path"],
            taxo_db_metadata_url=data["taxo_db_metadata_url"],
            tolerance=data["tolerance_ppm"] / 1e6,
        )
