from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class NetworkEnricherConfig:
    """Parameters for molecular networking."""

    mn_msms_mz_tol: float
    mn_score_cutoff: float
    mn_max_links: int
    mn_top_n: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NetworkEnricherConfig":
        """Creates an instance from a dictionary."""
        return NetworkEnricherConfig(
            mn_msms_mz_tol=data["mn_msms_mz_tol"],
            mn_score_cutoff=data["mn_score_cutoff"],
            mn_max_links=data["mn_max_links"],
            mn_top_n=data["mn_top_n"],
        )
