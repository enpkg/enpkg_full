"""Submodule for the ISDB enricher."""

from time import time
from typing import List
import pickle
from logging import Logger
import pandas as pd
from tqdm.auto import tqdm, trange
from tqdm.contrib import tzip
from downloaders import BaseDownloader

from matchms import calculate_scores
from matchms.similarity import ModifiedCosine
from matchms.networking import SimilarityNetwork
from matchms.filtering import default_filters
from matchms.filtering import normalize_intensities
from matchms.filtering import select_by_intensity
from matchms.filtering import select_by_mz
from matchms import Spectrum
from matchms.similarity import PrecursorMzMatch
from matchms.similarity import CosineGreedy
from monolith.enrichers.enricher import Enricher
from monolith.data import Analysis
from monolith.enrichers.adducts import (
    positive_adducts_from_chemical,
    negative_adducts_from_chemical,
)
from monolith.data import ISDBEnricherConfig
from monolith.data.isdb_data_classes import MS2ChemicalAnnotation
from monolith.data import Lotus
from monolith.data.isdb_data_classes import ChemicalAdduct
from monolith.utils import binary_search_by_key


def peak_processing(spectrum: Spectrum) -> Spectrum:
    """Applies peak processing to the spectrum.

    Parameters
    ----------
    spectrum : Spectrum
        The spectrum to process.
    """
    spectrum = default_filters(spectrum)
    spectrum = normalize_intensities(spectrum)
    spectrum = select_by_intensity(spectrum, intensity_from=0.01)
    spectrum = select_by_mz(spectrum, mz_from=10, mz_to=1000)
    return spectrum


class ISDBEnricher(Enricher):
    """Enricher that adds ISDB information to the analysis."""

    def __init__(
        self, configuration: ISDBEnricherConfig, polarity: bool, logger: Logger
    ):
        """Initializes the enricher."""
        assert isinstance(configuration, ISDBEnricherConfig)
        assert isinstance(polarity, bool)

        self.configuration = configuration
        self.polarity = polarity
        downloader = BaseDownloader()
        downloader.download(
            self.configuration.urls.taxo_db_metadata_url,
            "downloads/taxo_db_metadata.csv.gz",
        )
        logger.info("Loading Taxonomical Database metadata")
        start = time()
        lotus_metadata: pd.DataFrame = pd.read_csv(
            "downloads/taxo_db_metadata.csv", low_memory=False
        )
        logger.info(
            "Loaded %d Taxonomical Database metadata entries in %.2f seconds",
            len(lotus_metadata),
            time() - start,
        )
        start = time()
        logger.info(
            "Converting Taxonomical Database metadata DataFrame to Lotus objects"
        )
        Lotus.setup_lotus_columns(lotus_metadata.columns)
        self._lotus: List[Lotus] = [
            Lotus.from_pandas_series(row) for row in lotus_metadata.values
        ]
        logger.info(
            "Converted Taxonomical Database metadata DataFrame to Lotus objects in %.2f seconds",
            time() - start,
        )

        logger.info("Sorting Lotus entries by short inchikey")
        start = time()
        # We sort lotus by the short inchikey so that we can do binary search
        # of the spectral db inchikeys and align the two databases.
        self._lotus = sorted(self._lotus, key=lambda x: x.short_inchikey)
        logger.info(
            "Sorted Lotus entries by short inchikey in %.2f seconds", time() - start
        )

        downloader.download(
            self.configuration.urls.spectral_db_pos_url, "downloads/spectral_db_pos.pkl"
        )

        logger.info("Loading positive spectral database")
        start = time()
        with open("downloads/spectral_db_pos.pkl", "rb") as file:
            self._spectral_db_pos: List[Spectrum] = pickle.load(file)
        logger.info(
            "Loaded %d positive spectral database entries in %.2f seconds",
            len(self._spectral_db_pos),
            time() - start,
        )

        assert isinstance(self._spectral_db_pos, list)
        assert all(
            isinstance(spectrum, Spectrum) for spectrum in self._spectral_db_pos[:10]
        )
        assert all(
            spectrum.get("compound_name") is not None
            for spectrum in self._spectral_db_pos[:10]
        )

        # For each entry in the spectral database, we search for the Lotus entries with the
        # same short inchikey and add them as a list to the spectrum object metadata.
        # Since the Lotus entries are sorted by short inchikey, we can do binary search of
        # the spectrum short inchikeys and assign the slice of the Lotus entries with the same
        # short inchikey to the spectrum object.
        logger.info("Adding Lotus entries to spectral database")
        start = time()

        for spectrum in tqdm(
            self._spectral_db_pos,
            desc="Adding Lotus entries to spectral database",
            dynamic_ncols=True,
            leave=False,
        ):
            spectrum_short_inchikey = spectrum.get("compound_name")
            (found, smallest_idx) = binary_search_by_key(
                key=spectrum_short_inchikey,
                array=self._lotus,
                key_func=lambda x: x.short_inchikey,
            )

            if not found:
                continue

            # Since we may have landed exactly in the middle of an array of short inchikeys
            # with the same value, we need to identify the smallest index of the slice of
            # short inchikeys with the same value.

            while (
                smallest_idx > 0
                and self._lotus[smallest_idx - 1].short_inchikey
                == spectrum_short_inchikey
            ):
                smallest_idx -= 1

            largest_idx = smallest_idx

            while (
                largest_idx < len(self._lotus)
                and self._lotus[largest_idx].short_inchikey == spectrum_short_inchikey
            ):
                largest_idx += 1

            spectrum.set("lotus_entries", self._lotus[smallest_idx:largest_idx])

        logger.info(
            "Added Lotus entries to spectral database in %.2f seconds", time() - start
        )

        logger.info("Creating adducts")
        start = time()
        self._adducts: List[ChemicalAdduct] = (
            [
                adduct
                for lotus in self._lotus
                for adduct in positive_adducts_from_chemical(lotus)
            ]
            if polarity
            else [
                adduct
                for lotus in self._lotus
                for adduct in negative_adducts_from_chemical(lotus)
            ]
        )

        # We sort the adducts by the 'exact_mass' key so that when
        # we match the precursor mass with the adducts, we can do so
        # via binary search.

        self._adducts = sorted(self._adducts, key=lambda x: x.exact_mass)

        logger.info(
            "Created and sorted %d adducts in %.2f seconds",
            len(self._adducts),
            time() - start,
        )

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "ISDB Enricher"

    def enrich(self, analysis: Analysis) -> Analysis:
        """Adds ISDB information to the analysis."""

        similarities = calculate_scores(
            analysis.tandem_mass_spectra,
            analysis.tandem_mass_spectra,
            similarity_function=ModifiedCosine(
                tolerance=self.configuration.networking_params.mn_msms_mz_tol
            ),
            is_symmetric=True,
        )
        ms_network = SimilarityNetwork(
            identifier_key="scans",
            score_cutoff=self.configuration.networking_params.mn_score_cutoff,
            top_n=self.configuration.networking_params.mn_top_n,
            max_links=self.configuration.networking_params.mn_max_links,
            link_method="mutual",
        )
        ms_network.create_network(similarities, score_name="ModifiedCosine_score")

        analysis.set_molecular_network(ms_network.graph)

        similarity_score = PrecursorMzMatch(
            tolerance=self.configuration.spectral_match_params.parent_mz_tol,
            tolerance_type="Dalton",
        )
        cosinegreedy = CosineGreedy(
            tolerance=self.configuration.spectral_match_params.msms_mz_tol
        )

        range_size = 1000
        for min_range in trange(
            0,
            analysis.number_of_spectra,
            range_size,
            desc="Spectral matching",
            leave=False,
            dynamic_ncols=True,
        ):
            spectra_chunk = analysis.annotated_tandem_mass_spectra[
                min_range : min_range + range_size
            ]

            peak_processed_spectra = [
                peak_processing(spectrum.spectrum) for spectrum in spectra_chunk
            ]

            cosine_similarities_with_database = calculate_scores(
                peak_processed_spectra, self._spectral_db_pos, similarity_score
            )
            idx_row = cosine_similarities_with_database.scores[:, :][0]
            idx_col = cosine_similarities_with_database.scores[:, :][1]
            for x, y in tzip(
                idx_row, idx_col, desc="Processing chunk similarities", leave=False
            ):
                if x < y:
                    msms_score, n_matches = cosinegreedy.pair(
                        peak_processed_spectra[x], self._spectral_db_pos[y]
                    )[()]
                    if (
                        msms_score > self.configuration.spectral_match_params.min_score
                        and n_matches
                        > self.configuration.spectral_match_params.min_peaks
                    ):
                        spectra_chunk[x].add_annotation(
                            MS2ChemicalAnnotation(
                                cosine_similarity=msms_score,
                                number_of_matched_peaks=n_matches,
                                lotus=self._spectral_db_pos[y].get("lotus_entries"),
                            )
                        )

        for spectrum in tqdm(
            analysis.annotated_tandem_mass_spectra,
            leave=False,
            desc="Filtering precursor adducts",
            dynamic_ncols=True,
        ):
            spectrum.set_filtered_adducts_from_list(
                self._adducts,
                tolerance=self.configuration.spectral_match_params.parent_mz_tol,
            )

        return analysis
