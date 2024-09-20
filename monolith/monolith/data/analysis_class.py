"""
This submodule provides the Data Class for the analysis of the data.
An Analysis object contains the following data:
- raw_sha: str, the hash of the raw mass spec analysis data
- converted_sha: str, the hash of the converted mass spec analysis data
- sample_filename: str, the filename of the sample
- source_taxon: str, the taxon of the source
- tandem_mass_spectra: mgf.MgfFile, matchms-loaded mgf object
- features_quantification_table: pd.DataFrame, the quantification table of the features
- lcms_method_params: str, the parameters of the LCMS method
- lcms_processing_params: bs4.beautyfullsoup, the parameters of the LCMS processing
- metadata: pd.Series, the metadata Series of the analysis
"""

from typing import List, Tuple, Optional, Iterable
import pandas as pd
import numpy as np
import matchms
import networkx as nx
from monolith.data.annotated_spectra_class import AnnotatedSpectra
from monolith.data.otl_class import Match
from monolith.data.lotus_class import Lotus


class Analysis:
    """Data class for the analysis of the data."""

    def __init__(
        self,
        metadata: pd.Series,
        tandem_mass_spectra: List[matchms.Spectrum],
        features_quantification_table: pd.DataFrame,
    ):
        assert isinstance(metadata, pd.Series), "metadata must be a pd.Series object"
        assert (
            "sample_filename" in metadata
        ), "sample_filename is a required field in the metadata"
        assert (
            "source_taxon" in metadata
        ), "source_taxon is a required field in the metadata"
        assert (
            "sample_type" in metadata
        ), "sample_type is a required field in the metadata"
        assert metadata.sample_type in [
            "sample",
            "blank",
        ], "sample_type must be either 'sample' or 'blank'"
        assert isinstance(
            tandem_mass_spectra, list
        ), "tandem_mass_spectra must be a list"
        assert all(
            [isinstance(spectrum, matchms.Spectrum) for spectrum in tandem_mass_spectra]
        ), "tandem_mass_spectra must be a list of matchms.Spectrum objects"
        assert isinstance(
            features_quantification_table, pd.DataFrame
        ), "features_quantification_table must be a pd.DataFrame object"
        self._metadata = metadata
        self._tandem_mass_spectra = tandem_mass_spectra
        self._annotated_tandem_mass_spectra: List[AnnotatedSpectra] = [
            AnnotatedSpectra(
                spectrum,
                mass_over_charge=row["row m/z"],
                retention_time=row["row retention time"],
                intensity=row["Peak height"],
            )
            for (spectrum, (_, row)) in zip(
                tandem_mass_spectra, features_quantification_table.iterrows()
            )
        ]
        self._ott_matches: List[Match] = []
        self._molecular_network: Optional[nx.Graph] = None

    @property
    def sample_filename(self):
        return self._metadata["sample_filename"]

    @property
    def raw_source_taxon(self):
        return self._metadata["source_taxon"]

    @property
    def normalized_source_taxon(self):
        if not self.is_source_taxon_defined():
            raise ValueError("The source taxon is not defined.")
        return (
            self.raw_source_taxon.lower()
            .replace(" sp. ", " ")
            .replace(" x ", " ")
            .strip()
        )

    @property
    def number_of_spectra(self):
        return len(self._tandem_mass_spectra)

    @property
    def tandem_mass_spectra(self):
        return self._tandem_mass_spectra

    @property
    def annotated_tandem_mass_spectra(self):
        return self._annotated_tandem_mass_spectra

    @property
    def feature_ids(self) -> List[str]:
        """Returns the feature IDs of the analysis."""
        return [spectrum.feature_id for spectrum in self._annotated_tandem_mass_spectra]

    @property
    def number_of_spectra_with_at_least_one_annotation(self):
        return sum(
            int(spectrum.is_isdb_annotated())
            for spectrum in self._annotated_tandem_mass_spectra
        )

    @property
    def molecular_network(self):
        """Returns the molecular network of the analysis."""
        if self._molecular_network is None:
            raise ValueError("The molecular network is not set.")

        return self._molecular_network

    def set_molecular_network(self, molecular_network: nx.Graph):
        """Sets the molecular network of the analysis."""
        assert isinstance(
            molecular_network, nx.Graph
        ), "molecular_network must be a nx.Graph object"
        self._molecular_network = molecular_network

    @property
    def genus_and_species(self) -> Tuple[str, str]:
        """Returns a tuple of the genus and species of the source taxon."""
        taxon = self.normalized_source_taxon
        if " " not in taxon:
            raise ValueError("The source taxon does not have a genus and species.")
        return tuple(taxon.split(" ", 2)[:2])

    def is_source_taxon_defined(self) -> bool:
        """Returns whether the source taxon is defined."""
        return pd.notna(self.raw_source_taxon) and self.raw_source_taxon not in (
            "nd",
            "nan",
            "",
            None,
        )

    @property
    def sample_type(self):
        return self._metadata["sample_type"]

    def extend_ott_matches(self, ott_match: List[Match]):
        """Extends the OTT match of the analysis."""
        self._ott_matches.extend(ott_match)

    def set_isdb_propagated_npc_pathway_annotations(
        self, npc_pathway_annotations: np.ndarray
    ):
        """Sets the ISDB propagated pathway annotations"""
        for spectrum, npc_pathway_annotation in zip(
            self.annotated_tandem_mass_spectra, npc_pathway_annotations
        ):
            spectrum.set_isdb_propagated_npc_pathway_annotations(npc_pathway_annotation)

    def get_one_hot_encoded_npc_pathway_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC pathway annotations of the analysis."""
        return np.array(
            [
                spectrum.get_one_hot_encoded_npc_pathway_annotations()
                for spectrum in self.annotated_tandem_mass_spectra
            ]
        )

    def set_isdb_propagated_npc_superclass_annotations(
        self, npc_superclass_annotations: np.ndarray
    ):
        """Sets the ISDB propagated superclass annotations"""
        for spectrum, npc_superclass_annotation in zip(
            self.annotated_tandem_mass_spectra, npc_superclass_annotations
        ):
            spectrum.set_isdb_propagated_npc_superclass_annotations(
                npc_superclass_annotation
            )

    def get_one_hot_encoded_npc_superclass_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC superclass annotations of the analysis."""
        return np.array(
            [
                spectrum.get_one_hot_encoded_npc_superclass_annotations()
                for spectrum in self.annotated_tandem_mass_spectra
            ]
        )

    def set_isdb_propagated_npc_class_annotations(
        self, npc_class_annotations: np.ndarray
    ):
        """Sets the ISDB propagated class annotations"""
        for spectrum, npc_class_annotation in zip(
            self.annotated_tandem_mass_spectra, npc_class_annotations
        ):
            spectrum.set_isdb_propagated_npc_class_annotations(npc_class_annotation)

    def get_one_hot_encoded_npc_class_annotations(self) -> np.ndarray:
        """Returns the one-hot encoded NPC class annotations."""
        return np.array(
            [
                spectrum.get_one_hot_encoded_npc_class_annotations()
                for spectrum in self.annotated_tandem_mass_spectra
            ]
        )

    @property
    def best_ott_match(self) -> Match:
        """Returns the best OTT match of the analysis."""
        # TODO! UPDATE THIS SOMEHOW! Fo rexample by removing synonyms or taking only accepted names.
        return self._ott_matches[0]

    @property
    def best_lotus_annotation_per_spectra(self) -> Iterable[Lotus]:
        """Returns the best LOTUS annotation per spectra."""
        for spectrum in self.annotated_tandem_mass_spectra:
            if not spectrum.is_isdb_annotated():
                continue
            best_annotation = spectrum.best_lotus_annotation_by_ott_match(
                self.best_ott_match
            )

            if best_annotation is None:
                continue

            yield best_annotation
