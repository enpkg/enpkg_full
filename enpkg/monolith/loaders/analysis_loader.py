"""Loader utilities for creating Analysis objects from files."""

from pathlib import Path
from typing import Optional

import pandas as pd
from matchms.importing import load_from_mgf, load_from_mzml, load_from_mzxml

from enpkg.monolith.data.analysis import Analysis
from enpkg.monolith.data.sample_metadata import SampleMetadata


class AnalysisLoader:
    """Factory class for loading Analysis objects from files."""
    
    SUPPORTED_SPECTRA_FORMATS = {
        ".mgf": load_from_mgf,
        ".mzml": load_from_mzml,
        ".mzxml": load_from_mzxml,
    }
    
    RAW_EXTENSIONS = [".mzML", ".mzml", ".mzXML", ".mzxml"]

    @classmethod
    def from_files(
        cls,
        path_to_spectra: str,
        path_to_metadata: str,
        ionization_mode: str,
        run_name: Optional[str] = None,
    ) -> Analysis:
        """
        Creates an Analysis object from spectra and metadata files.
        
        Args:
            path_to_spectra: Path to the spectra file (.mgf, .mzML, .mzXML).
            path_to_metadata: Path to the metadata file (CSV/TSV).
            ionization_mode: Ionization mode, either 'pos' or 'neg'.
            run_name: Name of the run. If None, inferred from spectra filename.
            
        Returns:
            An Analysis instance.
            
        Raises:
            ValueError: If file format is unsupported or run_name not found in metadata.
        """
        path_to_spectra = Path(path_to_spectra)
        path_to_metadata = Path(path_to_metadata)
        
        # Load spectra
        spectra = cls._load_spectra(path_to_spectra)
        
        # Determine run name
        run_name = run_name or path_to_spectra.stem
        
        # Load and filter metadata
        metadata = cls._load_metadata(path_to_metadata, ionization_mode, run_name)
        
        return Analysis(
            run_name=run_name,
            spectra=spectra,
            metadata=metadata,
            ionization_mode=ionization_mode,
        )
    
    @classmethod
    def _load_spectra(cls, path: Path) -> tuple:
        """Load spectra from file."""
        suffix = path.suffix.lower()
        
        loader = cls.SUPPORTED_SPECTRA_FORMATS.get(suffix)
        if loader is None:
            supported = ", ".join(cls.SUPPORTED_SPECTRA_FORMATS.keys())
            raise ValueError(
                f"Unsupported spectra format: {suffix}. Supported: {supported}"
            )
        
        return tuple(loader(str(path)))
    
    @classmethod
    def _load_metadata(
        cls, 
        path: Path, 
        ionization_mode: str, 
        run_name: str
    ) -> SampleMetadata:
        """Load and filter metadata for the given run."""
        metadata_df = pd.read_csv(path, sep=None, engine="python")
        column_name = f"sample_filename_{ionization_mode}"
        
        for raw_ext in cls.RAW_EXTENSIONS:
            mask = metadata_df[column_name] == run_name + raw_ext
            filtered = metadata_df[mask]
            if not filtered.empty:
                return SampleMetadata.from_series(filtered.iloc[0])
        
        raise ValueError(
            f"Run name '{run_name}' not found in metadata for ionization mode '{ionization_mode}'"
        )
