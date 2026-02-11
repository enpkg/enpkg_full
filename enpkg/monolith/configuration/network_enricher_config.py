from pydantic import Field, model_validator
from typing import Self

from monolith.configuration.config import EnricherConfig

class NetworkEnricherConfig(EnricherConfig):
    """
    Configuration for the NetworkEnricher .
    """

    mn_msms_mz_tol: float = Field(
        0.01, 
        description="The parent mass tolerance to use for spectral matching (in Da) (if cosine)"
        )
    mn_score_cutoff: float = Field(
        0.7, 
        ge=0.0, 
        le=1.0, 
        description="The minimal modified cosine score for edge creation"
        )
    mn_top_n: int = Field(
        15, 
        gt=0,
        description="Maximum number of links to add per node"
        )
    mn_max_links: int = Field(
        10, 
        gt=0, 
        description="Consider edge between spectrumA and spectrumB if score falls into top_n for " \
        "spectrumA and spectrumB"
        )
    
    @model_validator(mode='after')
    def check_n_gt_max_links(self) -> Self:
        """Ensure mn_top_n is always greater than mn_max_links."""
        if self.mn_top_n <= self.mn_max_links:
            raise ValueError(
                f"mn_top_n ({self.mn_top_n}) must be greater than "
                f"mn_max_links ({self.mn_max_links})."
            )
        return self
