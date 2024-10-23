"""Submodule for the ISDB enricher."""

from time import time
from typing import List, Optional
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
from monolith.data.otl_class import Match
from monolith.utils import binary_search_by_key, label_propagation_algorithm


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
            [
                self.configuration.urls.taxo_db_metadata_url,
                self.configuration.urls.taxo_db_pathways_url,
                self.configuration.urls.taxo_db_superclasses_url,
                self.configuration.urls.taxo_db_classes_url,
            ],
            [
                self.configuration.paths.taxo_db_metadata_path,
                self.configuration.paths.taxo_db_pathways_path,
                self.configuration.paths.taxo_db_superclasses_path,
                self.configuration.paths.taxo_db_classes_path,
            ],
        )
        logger.info("Loading Taxonomical Database metadata")
        start = time()

        lotus_metadata: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_metadata_path, low_memory=False
        )
        lotus_metadata_pathways: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_pathways_path,
            index_col=0,
        )
        self._number_of_pathways = lotus_metadata_pathways.shape[1]
        self._pathways = lotus_metadata_pathways.columns
        lotus_metadata_superclasses: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_superclasses_path,
            index_col=0,
        )
        self._number_of_superclasses = lotus_metadata_superclasses.shape[1]
        self._superclasses = lotus_metadata_superclasses.columns
        lotus_metadata_classes: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_classes_path,
            index_col=0,
        )
        self._number_of_classes = lotus_metadata_classes.shape[1]
        self._classes = lotus_metadata_classes.columns
        logger.info(
            "Loaded %d Taxonomical Database metadata entries in %.2f seconds",
            len(lotus_metadata),
            time() - start,
        )
        start = time()
        logger.info(
            "Converting Taxonomical Database metadata DataFrame to Lotus objects"
        )
        structure_smiles_column_number: int = lotus_metadata.columns.get_loc(
            "structure_smiles"
        )
        Lotus.setup_lotus_columns(list(lotus_metadata.columns))
        self._lotus: List[Lotus] = [
            Lotus.from_pandas_series(
                list(row),
                pathways=lotus_metadata_pathways.loc[
                    row[structure_smiles_column_number]
                ],
                superclasses=lotus_metadata_superclasses.loc[
                    row[structure_smiles_column_number]
                ],
                classes=lotus_metadata_classes.loc[row[structure_smiles_column_number]],
            )
            for row in lotus_metadata.values
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
                                number_of_matched_peaks=int(n_matches),
                                lotus=self._spectral_db_pos[y].get("lotus_entries"),
                            )
                        )

        pathway_features = np.zeros(
            (analysis.number_of_spectra, self._number_of_pathways), dtype=np.float32
        )
        superclass_features = np.zeros(
            (analysis.number_of_spectra, self._number_of_superclasses),
            dtype=np.float32,
        )
        class_features = np.zeros(
            (analysis.number_of_spectra, self._number_of_classes), dtype=np.float32
        )

        best_ott_match: Optional[Match] = analysis.best_ott_match

        for i, spectrum in enumerate(analysis.tandem_mass_spectra):

            # If the spectrum has no ISDB annotations, we cannot make assumptions regarding its scores,
            # and therefore we give uniform scores to all pathways, superclasses, and classes.
            if not spectrum.has_isdb_annotations():
                continue

            # Now that we have determined the candidates potentially associated with this
            # spectrum, we can populate the associated features with the candidates' pathway,
            # superclass, and class annotations, weighted by the adduct's normalized
            # taxonomical similarity score.

            chemical_similarities: np.ndarray = np.fromiter(
                (
                    annotation.cosine_similarity
                    for annotation in spectrum.isdb_annotations
                    if annotation.has_lotus_entries()
                ),
                dtype=np.float32,
            )

            if best_ott_match is not None:
                taxonomical_similarities: np.ndarray = np.fromiter(
                    (
                        annotation.maximal_normalized_taxonomical_similarity(
                            best_ott_match
                        )
                        for annotation in spectrum.isdb_annotations
                        if annotation.has_lotus_entries()
                    ),
                    dtype=np.float32,
                )
            else:
                taxonomical_similarities = np.ones(
                    (chemical_similarities.size,), dtype=np.float32
                )

            combined_similarities: np.ndarray = (
                taxonomical_similarities * chemical_similarities
            )

            # We normalize the combined similarity scores
            combined_similarities /= np.sum(combined_similarities)

            for isdb_annotation, combined_similarity in zip(
                (
                    annotation
                    for annotation in spectrum.isdb_annotations
                    if annotation.has_lotus_entries()
                ),
                combined_similarities,
            ):
                pathway_features[i] += (
                    combined_similarity * isdb_annotation.get_hammer_pathway_scores()
                )
                superclass_features[i] += (
                    combined_similarity * isdb_annotation.get_hammer_superclass_scores()
                )
                class_features[i] += (
                    combined_similarity * isdb_annotation.get_hammer_class_scores()
                )

        pathway = pd.DataFrame(pathway_features, columns=self._pathways)
        pathway.to_csv("downloads/before_lpa_isdb_pathway.csv", index=False)
        superclass = pd.DataFrame(superclass_features, columns=self._superclasses)
        superclass.to_csv("downloads/before_lpa_isdb_superclass.csv", index=False)
        classes = pd.DataFrame(class_features, columns=self._classes)
        classes.to_csv("downloads/before_lpa_isdb_class.csv", index=False)

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
            normalize=False,
        )

        loading_bar.update(1)

        propagated_superclass = label_propagation_algorithm(
            graph=analysis.molecular_network,
            node_names=analysis.feature_ids,
            features=superclass_features,
            normalize=False,
        )

        loading_bar.update(1)

        propagated_class = label_propagation_algorithm(
            graph=analysis.molecular_network,
            node_names=analysis.feature_ids,
            features=class_features,
            normalize=False,
        )

        loading_bar.update(1)
        loading_bar.close()

        for i, spectrum in enumerate(analysis.tandem_mass_spectra):
            spectrum.set_isdb_hammer_pathway_scores(propagated_pathway[i])
            spectrum.set_isdb_hammer_superclass_scores(propagated_superclass[i])
            spectrum.set_isdb_hammer_class_scores(propagated_class[i])

        # THIS SHOULD BE DELETED AFTERWARDS! DO NOT KEEP THIS!

        pathway = pd.DataFrame(propagated_pathway, columns=self._pathways)
        pathway.to_csv("downloads/isdb_pathway.csv", index=False)
        superclass = pd.DataFrame(propagated_superclass, columns=self._superclasses)
        superclass.to_csv("downloads/isdb_superclass.csv", index=False)
        classes = pd.DataFrame(propagated_class, columns=self._classes)
        classes.to_csv("downloads/isdb_class.csv", index=False)

        return analysis
