"""Submodule for the ISDB enricher."""

from typing import Dict, List
from opentree import OT
import requests
import yaml
import pickle
import pandas as pd
from tqdm.auto import tqdm, trange
from tqdm.contrib import tzip
from monolith.data import ISDBEnricherConfig
from monolith.data.isdb_data_classes import ChemicalAnnotation, AnnotatedSpectra
from monolith.data.analysis_class import Analysis
from monolith.enrichers.enricher import Enricher
from downloaders import BaseDownloader

import os
import numpy as np
import pandas as pd
from matchms import calculate_scores
from matchms.similarity import ModifiedCosine
from matchms.networking import SimilarityNetwork
from matchms.filtering import default_filters
from matchms.filtering import normalize_intensities
from matchms.filtering import select_by_intensity
from matchms.filtering import select_by_mz
from matchms import Spectrum
from matchms.similarity import PrecursorMzMatch
from matchms import calculate_scores
from matchms.similarity import CosineGreedy
from matchms.logging_functions import set_matchms_logger_level
import networkx as nx


def peak_processing(spectrum: Spectrum) -> Spectrum:
    spectrum = default_filters(spectrum)
    spectrum = normalize_intensities(spectrum)
    spectrum = select_by_intensity(spectrum, intensity_from=0.01)
    spectrum = select_by_mz(spectrum, mz_from=10, mz_to=1000)
    return spectrum


class ISDBEnricher(Enricher):
    """Enricher that adds ISDB information to the analysis."""

    def __init__(self, configuration: ISDBEnricherConfig):
        """Initializes the enricher."""
        self.configuration = configuration
        downloader = BaseDownloader()
        downloader.download(
            self.configuration.urls.taxo_db_metadata_url,
            "downloads/taxo_db_metadata.csv.gz",
        )
        self._taxo_db_metadata = pd.read_csv(
            "downloads/taxo_db_metadata.csv", low_memory=False
        )

        downloader.download(
            self.configuration.urls.spectral_db_pos_url, "downloads/spectral_db_pos.pkl"
        )

        with open("downloads/spectral_db_pos.pkl", "rb") as file:
            self._spectral_db_pos = pickle.load(file)

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
                            ChemicalAnnotation(
                                cosine_similarity=msms_score,
                                number_of_matched_peaks=n_matches,
                                molecule_id=y + 1,
                                short_inchikey=self._spectral_db_pos[y].get(
                                    "compound_name"
                                ),
                            )
                        )
