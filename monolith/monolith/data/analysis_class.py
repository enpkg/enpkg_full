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

from typing import Tuple, Optional
import pandas as pd
import matchms
import networkx as nx
from monolith.data.annotated_spectra_class import AnnotatedSpectrum
from monolith.data.otl_class import Match


class Analysis:
    """Data class for the analysis of the data."""

    def __init__(
        self,
        metadata: pd.Series,
        tandem_mass_spectra: list[matchms.Spectrum],
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
        self._tandem_mass_spectra: list[AnnotatedSpectrum] = [
            AnnotatedSpectrum(
                spectrum,
                mass_over_charge=row["row m/z"],
                retention_time=row["row retention time"],
                intensity=row["Peak height"],
            )
            for (spectrum, (_, row)) in zip(
                tandem_mass_spectra, features_quantification_table.iterrows()
            )
        ]
        self._ott_matches: list[Match] = []
        self._molecular_network: Optional[nx.Graph] = None

    @property
    def sample_filename(self):
        """Returns the filename of the sample."""
        return self._metadata["sample_filename"]

    @property
    def raw_source_taxon(self):
        """Returns the raw source taxon of the analysis."""
        return self._metadata["source_taxon"]

    @property
    def normalized_source_taxon(self):
        """Returns the normalized source taxon of the analysis."""
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
        """Returns the number of tandem mass spectra of the analysis."""
        return len(self._tandem_mass_spectra)

    @property
    def tandem_mass_spectra(self) -> list[AnnotatedSpectrum]:
        """Returns the tandem mass spectra of the analysis."""
        return self._tandem_mass_spectra

    @property
    def feature_ids(self) -> list[str]:
        """Returns the feature IDs of the analysis."""
        return [spectrum.feature_id for spectrum in self._tandem_mass_spectra]

    @property
    def number_of_spectra_with_at_least_one_annotation(self):
        """Returns the number of spectra with at least one annotation."""
        return sum(
            int(spectrum.has_isdb_annotations())
            for spectrum in self._tandem_mass_spectra
        )

    @property
    def molecular_network(self):
        """Returns the molecular network of the analysis."""
        if self._molecular_network is None:
            raise RuntimeError("The molecular network is not set.")

        return self._molecular_network

    def set_molecular_network(self, molecular_network: nx.Graph):
        """Sets the molecular network of the analysis."""
        # We check that the number of nodes in the network
        # is the same as the number of spectra in the analysis
        assert len(molecular_network.nodes) == self.number_of_spectra, (
            f"The number of nodes in the network ({len(molecular_network.nodes)}) "
            f"must be the same as the number of spectra in the analysis ({self.number_of_spectra})."
        )
        # We check that the names of the nodes in the network
        # are the same as the feature IDs of the spectra
        assert set(molecular_network.nodes) == set(self.feature_ids), (
            f"The nodes in the network ({set(molecular_network.nodes)}) "
            f"must be the same as the feature IDs of the spectra ({set(self.feature_ids)})."
        )
        # We check that the order of the nodes in the network
        # is the same as the order of the spectra in the analysis
        assert all(
            node == feature_id
            for node, feature_id in zip(molecular_network.nodes, self.feature_ids)
        ), (
            "The order of the nodes in the network must be the same "
            "as the order of the spectra in the analysis."
        )

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
        """Returns the sample type of the analysis."""
        return self._metadata["sample_type"]

    def extend_ott_matches(self, ott_match: list[Match]):
        """Extends the OTT match of the analysis."""
        self._ott_matches.extend(ott_match)

    @property
    def best_ott_match(self) -> Optional[Match]:
        """Returns the best OTT match of the analysis.

        In some cases, there may not be a best OTT match, in which case None is returned.
        """
        if not self._ott_matches:
            return None

        # TODO! UPDATE THIS SOMEHOW! Fo rexample by removing synonyms or taking only accepted names.
        return self._ott_matches[0]

    def to_dataframe(self) -> pd.DataFrame:
        """Returns the analysis as a DataFrame."""
        return pd.DataFrame([
            spectrum.into_dict(self.best_ott_match)
            for spectrum in self._tandem_mass_spectra
        ])
