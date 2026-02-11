"""Sample metadata model for Analysis."""

from typing import Optional
from pydantic import BaseModel, field_validator
import pandas as pd


class SampleMetadata(BaseModel):
    """
    Structured metadata for an analysis sample.
    
    This replaces the unstructured pd.Series approach with explicit,
    validated fields.
    """
    
    sample_id: str
    source_taxon: Optional[str] = None
    sample_type: Optional[str] = None
    source_id: Optional[str] = None
    organism_kingdom: Optional[str] = None
    organism_phylum: Optional[str] = None
    organism_class: Optional[str] = None
    organism_order: Optional[str] = None
    organism_family: Optional[str] = None
    organism_genus: Optional[str] = None

    # TODO: Externalize these fields
    analysis_filename_pos: Optional[str] = None
    analysis_filename_neg: Optional[str] = None
    massive_id: Optional[str] = None
    
    # Store any additional fields not explicitly defined
    extra_fields: dict = {}

    @field_validator("source_taxon", mode="before")
    @classmethod
    def normalize_source_taxon(cls, value):
        """Normalize empty/invalid source taxon values to None."""
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        if isinstance(value, str) and value.lower() in ("nd", "nan", ""):
            return None
        return value

    @classmethod
    def from_series(cls, series: pd.Series) -> "SampleMetadata":
        """
        Create SampleMetadata from a pandas Series (e.g., a row from a DataFrame).
        
        Known fields are extracted explicitly; unknown fields go to extra_fields.
        """
        known_fields = {
            "sample_id", "source_taxon", "sample_type", "source_id",
            "organism_kingdom", "organism_phylum", "organism_class",
            "organism_order", "organism_family", "organism_genus",
            "analysis_filename_pos", "analysis_filename_neg", "massive_id"
        }
        
        data = series.to_dict()
        known_data = {k: v for k, v in data.items() if k in known_fields}
        extra_data = {k: v for k, v in data.items() if k not in known_fields}
        
        # Convert NaN values to None for known fields
        for key, value in known_data.items():
            if isinstance(value, float) and pd.isna(value):
                known_data[key] = None
        
        return cls(**known_data, extra_fields=extra_data)
    
    def has_source_taxon(self) -> bool:
        """Returns True if source_taxon is defined and valid."""
        return self.source_taxon is not None
