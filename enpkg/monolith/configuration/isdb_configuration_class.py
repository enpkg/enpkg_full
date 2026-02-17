"""Configuration classes for ISDB enrichment."""

from typing import Optional
from pydantic import BaseModel, Field, model_validator
from typing import Self

from enpkg.monolith.configuration.config import EnricherConfig


class GeneralParams(BaseModel):
    """General processing parameters."""

    recompute: bool = Field(
        default=False,
        description="Whether to recompute results even if they already exist"
    )
    redownload_if_exists: list | bool = Field(
        default=False,
        description="Whether to redownload database files if they already exist locally"
    )
    


class Urls(BaseModel):
    """URLs for remote data files."""

    taxo_db_metadata: Optional[str] = Field(
        default=None,
        description="URL for taxonomic database metadata"
    )
    spectral_db_pos: Optional[str] = Field(
        default=None,
        description="URL for positive mode spectral database"
    )
    spectral_db_neg: Optional[str] = Field(
        default=None,
        description="URL for negative mode spectral database"
    )
    taxo_db_pathways: Optional[str] = Field(
        default=None,
        description="URL for taxonomic pathways database"
    )
    taxo_db_superclasses: Optional[str] = Field(
        default=None,
        description="URL for taxonomic superclasses database"
    )
    taxo_db_classes: Optional[str] = Field(
        default=None,
        description="URL for taxonomic classes database"
    )

    @property
    def empty(self) -> bool:
        """Check if all URLs are None."""
        return all(
            getattr(self, field_name) is None
            for field_name in self.model_fields
        )

    def __iter__(self):
        """Iterate over non-None URL values."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                yield value

    def items(self):
        """Iterate over (field_name, url) pairs for non-None URLs."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                yield field_name, value

    def __len__(self) -> int:
        """Return count of non-None URLs."""
        return sum(1 for _ in self)


class Paths(BaseModel):
    """Local paths to data files."""

    taxo_db_metadata: Optional[str] = Field(
        default=None,
        description="Local path for taxonomic database metadata"
    )
    spectral_db_pos: Optional[str]  = Field(
        default=None,
        description="Local path for positive mode spectral database"
    )
    spectral_db_neg: Optional[str] = Field(
        default=None,
        description="Local path for negative mode spectral database"
    )
    taxo_db_pathways: Optional[str] = Field(
        default=None,
        description="Local path for taxonomic pathways database"
    )
    taxo_db_superclasses: Optional[str] = Field(
        default=None,
        description="Local path for taxonomic superclasses database"
    )
    taxo_db_classes: Optional[str] = Field(
        default=None,
        description="Local path for taxonomic classes database"
    )


    def path_list(self) -> list[str]:
        """Return list of all defined paths."""
        return [
            getattr(self, field_name)
            for field_name in self.model_fields
            if getattr(self, field_name) is not None
        ]

    def __iter__(self):
        """Iterate over non-None path values."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                yield value

    def items(self):
        """Iterate over (field_name, path) pairs for non-None paths."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if value is not None:
                yield field_name, value

    def __len__(self) -> int:
        """Return count of non-None paths."""
        return sum(1 for _ in self)


class SpectralMatchParams(BaseModel):
    """Parameters for spectral matching."""

    parent_mz_tol: float = Field(
        default=0.01,
        gt=0,
        description="Parent mass tolerance for spectral matching (in Da)"
    )
    msms_mz_tol: float = Field(
        default=0.01,
        gt=0,
        description="MS/MS fragment mass tolerance (in Da)"
    )
    min_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum spectral similarity score for a match"
    )
    min_peaks: int = Field(
        default=6,
        ge=1,
        description="Minimum number of matching peaks required"
    )


class ReweightingParams(BaseModel):
    """Parameters for result reweighting and scoring."""

    top_to_output: int = Field(
        default=5,
        ge=1,
        description="Number of top candidates to output"
    )
    use_post_taxo: bool = Field(
        default=True,
        description="Whether to use post-processing taxonomic filtering"
    )
    top_N_chemical_consistency: int = Field(
        default=5,
        ge=1,
        description="Number of top candidates for chemical consistency scoring"
    )
    min_score_taxo_ms1: float = Field(
        default=0,
        ge=0,
        description="Minimum taxonomic score for MS1 matches"
    )
    min_score_chemo_ms1: float = Field(
        default=0,
        ge=0,
        description="Minimum chemical score for MS1 matches"
    )
    msms_weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Weight for MS/MS spectral similarity in final score"
    )
    taxo_weight: float = Field(
        default=0.5,
        ge=0.0,
        description="Weight for taxonomic scoring in final score"
    )
    chemo_weight: float = Field(
        default=0.5,
        ge=0.0,
        description="Weight for chemical consistency in final score"
    )

    @model_validator(mode='after')
    def validate_weights_sum(self) -> Self:
        """Warn if weights don't sum to a reasonable value."""
        total = self.msms_weight + self.taxo_weight + self.chemo_weight
        if total == 0:
            raise ValueError("At least one weight must be greater than 0")
        return self


class ISDBEnricherConfig(EnricherConfig, BaseModel):
    """Configuration for ISDB Enrichers.
    
    Combines all sub-configurations for spectral matching against
    the In-Silico DataBase with taxonomic and chemical reweighting.
    """

    general_params: GeneralParams = Field(
        default_factory=GeneralParams,
        description="General processing parameters"
    )
    paths: Paths = Field(
        ...,
        description="Local file paths for databases"
    )
    urls: Optional[Urls] = Field(
        default=None,
        description="Remote URLs for database downloads (optional)"
    )
    spectral_match_params: SpectralMatchParams = Field(
        default_factory=SpectralMatchParams,
        description="Parameters for spectral matching"
    )
    reweighting_params: ReweightingParams = Field(
        default_factory=ReweightingParams,
        description="Parameters for score reweighting"
    )
