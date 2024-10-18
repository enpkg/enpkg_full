from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class GeneralParams:
    """General processing parameters."""

    recompute: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeneralParams":
        """Creates an instance from a dictionary."""
        return GeneralParams(recompute=data["recompute"])


@dataclass
class Urls:
    """URLs for data files."""

    taxo_db_metadata_url: str
    spectral_db_pos_url: str
    taxo_db_pathways_url: str
    taxo_db_superclasses_url: str
    taxo_db_classes_url: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Urls":
        """Creates an instance from a dictionary."""
        return cls(
            taxo_db_metadata_url=data["taxo_db_metadata_url"],
            spectral_db_pos_url=data["spectral_db_pos_url"],
            taxo_db_pathways_url=data["taxo_db_pathways_url"],
            taxo_db_superclasses_url=data["taxo_db_superclasses_url"],
            taxo_db_classes_url=data["taxo_db_classes_url"],
        )


@dataclass
class Paths:
    """Paths to data files."""

    taxo_db_metadata_path: str
    spectral_db_pos_path: str
    spectral_db_neg_path: str
    taxo_db_pathways_path: str
    taxo_db_superclasses_path: str
    taxo_db_classes_path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paths":
        """Creates an instance from a dictionary."""
        return cls(
            taxo_db_metadata_path=data["taxo_db_metadata_path"],
            spectral_db_pos_path=data["spectral_db_pos_path"],
            spectral_db_neg_path=data["spectral_db_neg_path"],
            taxo_db_pathways_path=data["taxo_db_pathways_path"],
            taxo_db_superclasses_path=data["taxo_db_superclasses_path"],
            taxo_db_classes_path=data["taxo_db_classes_path"],
        )


@dataclass
class SpectralMatchParams:
    """Parameters for spectral matching."""

    parent_mz_tol: float
    msms_mz_tol: float
    min_score: float
    min_peaks: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpectralMatchParams":
        """Creates an instance from a dictionary."""
        return cls(
            parent_mz_tol=data["parent_mz_tol"],
            msms_mz_tol=data["msms_mz_tol"],
            min_score=data["min_score"],
            min_peaks=data["min_peaks"],
        )


@dataclass
class ReweightingParams:
    """Parameters for result reweighting."""

    top_to_output: int
    use_post_taxo: bool
    top_N_chemical_consistency: int
    min_score_taxo_ms1: int
    min_score_chemo_ms1: int
    msms_weight: float
    taxo_weight: float
    chemo_weight: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReweightingParams":
        """Creates an instance from a dictionary."""
        return cls(
            top_to_output=data["top_to_output"],
            use_post_taxo=data["use_post_taxo"],
            top_N_chemical_consistency=data["top_N_chemical_consistency"],
            min_score_taxo_ms1=data["min_score_taxo_ms1"],
            min_score_chemo_ms1=data["min_score_chemo_ms1"],
            msms_weight=data["msms_weight"],
            taxo_weight=data["taxo_weight"],
            chemo_weight=data["chemo_weight"],
        )


@dataclass
class ISDBEnricherConfig:
    """Configuration for IDB Enrichers."""

    general_params: GeneralParams
    paths: Paths
    urls: Urls
    spectral_match_params: SpectralMatchParams
    reweighting_params: ReweightingParams

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ISDBEnricherConfig":
        """Creates an instance from a dictionary."""
        return cls(
            general_params=GeneralParams.from_dict(data["general_params"]),
            paths=Paths.from_dict(data["paths"]),
            urls=Urls.from_dict(data["urls"]),
            spectral_match_params=SpectralMatchParams.from_dict(
                data["spectral_match_params"]
            ),
            reweighting_params=ReweightingParams.from_dict(data["reweighting_params"]),
        )
