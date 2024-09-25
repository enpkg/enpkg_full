"""Submodule for the ISDB enricher."""

from time import time
from typing import List
import pickle
from logging import Logger
import pandas as pd
import numpy as np
from tqdm.auto import tqdm, trange
from tqdm.contrib import tzip
from downloaders import BaseDownloader

from matchms import calculate_scores
from matchms.similarity import PrecursorMzMatch
from matchms.similarity import CosineGreedy
from matchms import Spectrum
from monolith.enrichers.enricher import Enricher
from monolith.data import Analysis
from monolith.data.annotated_spectra_class import AnnotatedSpectrum
from monolith.data import ISDBEnricherConfig
from monolith.data.isdb_data_classes import ISDBChemicalAnnotation
from monolith.data.lotus_class import Lotus
from monolith.utils import binary_search_by_key, label_propagation_algorithm
from monolith.data.lotus_class import (
    NUMBER_OF_NPC_PATHWAYS,
    NUMBER_OF_NPC_SUPERCLASSES,
    NUMBER_OF_NPC_CLASSES,
    NPC_PATHWAYS,
    NPC_SUPERCLASSES,
    NPC_CLASSES,
)


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

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "ISDB Enricher"

    def enrich(self, analysis: Analysis) -> Analysis:
        """Adds ISDB information to the analysis."""
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
            spectra_chunk: List[AnnotatedSpectrum] = analysis.tandem_mass_spectra[
                min_range : min_range + range_size
            ]

            cosine_similarities_with_database = calculate_scores(
                references=spectra_chunk,
                queries=self._spectral_db_pos,
                similarity_function=similarity_score,
            )

            idx_reference = cosine_similarities_with_database.scores[:, :][0]
            idx_query = cosine_similarities_with_database.scores[:, :][1]
            for x, y in tzip(
                idx_reference,
                idx_query,
                desc="Processing chunk similarities",
                leave=False,
            ):
                if x < y:
                    msms_score, n_matches = cosinegreedy.pair(
                        spectra_chunk[x], self._spectral_db_pos[y]
                    )[()]
                    if (
                        msms_score > self.configuration.spectral_match_params.min_score
                        and n_matches
                        > self.configuration.spectral_match_params.min_peaks
                    ):
                        spectra_chunk[x].add_isdb_annotation(
                            ISDBChemicalAnnotation(
                                cosine_similarity=msms_score,
                                number_of_matched_peaks=n_matches,
                                lotus=self._spectral_db_pos[y].get("lotus_entries"),
                            )
                        )

        pathway_features = np.zeros(
            (analysis.number_of_spectra, NUMBER_OF_NPC_PATHWAYS), dtype=np.float32
        )
        superclass_features = np.zeros(
            (analysis.number_of_spectra, NUMBER_OF_NPC_SUPERCLASSES),
            dtype=np.float32,
        )
        class_features = np.zeros(
            (analysis.number_of_spectra, NUMBER_OF_NPC_CLASSES), dtype=np.float32
        )

        for i, spectrum in enumerate(analysis.tandem_mass_spectra):

            # If the spectrum has no ISDB annotations, we cannot make assumptions regarding its scores,
            # and therefore we give uniform scores to all pathways, superclasses, and classes.
            if not spectrum.has_isdb_annotations():
                pathway_features[i] = np.zeros(
                    (NUMBER_OF_NPC_PATHWAYS,),
                )
                superclass_features[i] = np.zeros(
                    (NUMBER_OF_NPC_SUPERCLASSES,),
                )
                class_features[i] = np.zeros((NUMBER_OF_NPC_CLASSES,))
                continue

            # Now that we have determined the candidates potentially associated with this
            # spectrum, we can populate the associated features with the candidates' pathway,
            # superclass, and class annotations, weighted by the adduct's normalized
            # taxonomical similarity score.
            for isdb_annotation in spectrum.isdb_annotations:
                pathway_features[i] += isdb_annotation.get_npc_pathway_scores(
                    analysis.best_ott_match
                )

                superclass_features[i] += isdb_annotation.get_npc_superclass_scores(
                    analysis.best_ott_match
                )

                class_features[i] += isdb_annotation.get_npc_class_scores(
                    analysis.best_ott_match
                )

            # We normalize by the number of ISDB annotations
            pathway_features[i] /= len(spectrum.isdb_annotations)
            superclass_features[i] /= len(spectrum.isdb_annotations)
            class_features[i] /= len(spectrum.isdb_annotations)

        loading_bar = tqdm(
            desc="Computing LPA scores",
            dynamic_ncols=True,
            leave=False,
            total=3,
        )

        propagated_pathway = label_propagation_algorithm(
            graph=analysis.molecular_network,
            node_names=analysis.feature_ids,
            features=pathway_features,
        )

        loading_bar.update(1)

        propagated_superclass = label_propagation_algorithm(
            graph=analysis.molecular_network,
            node_names=analysis.feature_ids,
            features=superclass_features,
        )

        loading_bar.update(1)

        propagated_class = label_propagation_algorithm(
            graph=analysis.molecular_network,
            node_names=analysis.feature_ids,
            features=class_features,
        )

        loading_bar.update(1)
        loading_bar.close()

        for i, spectrum in enumerate(analysis.tandem_mass_spectra):
            spectrum.set_isdb_npc_pathway_scores(propagated_pathway[i])
            spectrum.set_isdb_npc_superclass_scores(propagated_superclass[i])
            spectrum.set_isdb_npc_class_scores(propagated_class[i])

        # THIS SHOULD BE DELETED AFTERWARDS! DO NOT KEEP THIS!

        pathway = pd.DataFrame(propagated_pathway, columns=NPC_PATHWAYS)
        pathway.to_csv("downloads/isdb_pathway.csv", index=False)
        superclass = pd.DataFrame(propagated_superclass, columns=NPC_SUPERCLASSES)
        superclass.to_csv("downloads/isdb_superclass.csv", index=False)
        classes = pd.DataFrame(propagated_class, columns=NPC_CLASSES)
        classes.to_csv("downloads/isdb_class.csv", index=False)

        return analysis
