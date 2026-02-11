"""Submodule for the ISDB enricher."""

import logging
from pathlib import Path
from time import time
from typing import Optional, NamedTuple
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
from enpkg.monolith.enrichers.enricher import Enricher
from enpkg.monolith.data.analysis import Analysis
from enpkg.monolith.data.annotated_spectra_class import AnnotatedSpectrum
from enpkg.monolith.data.isdb_data_classes.isdb_configuration_class import ISDBEnricherConfig, GeneralParams, Urls, Paths
from enpkg.monolith.data.isdb_data_classes import ISDBChemicalAnnotation
from enpkg.monolith.data.lotus_class import Lotus
from enpkg.monolith.data.otl_class import Match
from enpkg.monolith.utils import binary_search_by_key, label_propagation_algorithm
from enpkg.monolith.exceptions import DBLoaderError

# Valid URL field names that can be used in redownload_if_exists
VALID_URL_FIELDS: list[str] = [
    "taxo_db_metadata",
    "spectral_db_pos",
    "spectral_db_neg",
    "taxo_db_pathways",
    "taxo_db_superclasses",
    "taxo_db_classes",
]


class DownloadInfo(NamedTuple):
    """Container for database download information."""
    field_name: str
    url: str
    local_path: str


class DBLoader:
    """
    Loader for the different databases (ISDB, Taxonomical, etc).
    """

    def __init__(self, configuration: ISDBEnricherConfig, logger: Logger):

        self.configuration = configuration
        self.logger = logger
        self.downloads: list[DownloadInfo] = []

        if self.configuration.urls is not None:
            self._validate_redownload_fields()
            self._collect_downloads()
            if self.downloads:
                self._download_databases()

    def _validate_redownload_fields(self) -> None:
        """Validate that redownload_if_exists contains only valid URL field names."""
        
        redownload = self.configuration.general_params.redownload_if_exists
        
        # If it's a boolean, no validation needed
        if isinstance(redownload, bool):
            return
        
        # If it's a list, validate each field name
        if isinstance(redownload, list):
            invalid_fields = [field for field in redownload if field not in VALID_URL_FIELDS]
            if invalid_fields:
                raise DBLoaderError(
                    f"Invalid field name(s): {invalid_fields}. "
                    f"Valid fields are: {VALID_URL_FIELDS}"
                )

    def _collect_downloads(self) -> None:
        """Match URLs to their corresponding local paths by field name."""
        
        for field_name, url in self.configuration.urls.items():
            local_path = getattr(self.configuration.paths, field_name, None)
            if local_path is not None:
                self.downloads.append(DownloadInfo(field_name, url, local_path))
            else:
                self.logger.warning(
                    f"No local path defined for URL '{field_name}'; skipping download"
                )

    def _download_databases(self) -> None:
        """Download databases from URLs to local paths."""

        self.logger.info(f"Downloading {len(self.downloads)} databases")
        downloader = BaseDownloader()
        for download in self.downloads:
            try:
                p = Path(download.local_path)
                redownload = self.configuration.general_params.redownload_if_exists
                should_redownload = (
                    redownload is True or 
                    (isinstance(redownload, list) and download.field_name in redownload)
                )
                
                if p.is_file() and not should_redownload:
                    self.logger.info(
                        f"Database at {download.local_path} already exists; skipping download"
                    )
                else:
                    downloader.download(download.url, download.local_path)
                    self.logger.info(f"Downloaded database from {download.url} to {download.local_path}")
                    
            except Exception as e:
                self.logger.error(
                    f"Failed to download database from {download.url} to {download.local_path}: {str(e)}"
                )
        self.logger.info("Databases downloaded successfully")

    def load_taxonomical_databases(self) -> None:
        """Load databases into memory."""

        self.logger.info("Loading databases into memory")
        
        start = time()
        self.lotus_metadata: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_metadata, low_memory=False
        )
        self.logger.info(f"Loaded Taxonomical Database metadata in {time() - start:.2f} seconds")
        self.logger.debug(f"Loaded Taxonomical Database metadata with columns: {self.lotus_metadata.columns.tolist()}")
        
        start = time()
        self.lotus_metadata_pathways: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_pathways,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database pathways in {time() - start:.2f} seconds")
        self._number_of_pathways = self.lotus_metadata_pathways.shape[1]
        self._pathways = self.lotus_metadata_pathways.columns
        
        start = time()
        self.lotus_metadata_superclasses: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_superclasses,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database superclasses in {time() - start:.2f} seconds")
        self._number_of_superclasses = self.lotus_metadata_superclasses.shape[1]
        self._superclasses = self.lotus_metadata_superclasses.columns
        
        start = time()
        self.lotus_metadata_classes: pd.DataFrame = pd.read_csv(
            self.configuration.paths.taxo_db_classes,
            index_col=0,
        )
        self.logger.info(f"Loaded Taxonomical Database classes in {time() - start:.2f} seconds")
        self._number_of_classes = self.lotus_metadata_classes.shape[1]
        self._classes = self.lotus_metadata_classes.columns
        
        self.logger.info(
            "Loaded %d Taxonomical Database metadata entries",
            len(self.lotus_metadata),
        )

    def load_spectral_databases(self, mode) -> None:
        """Load spectral databases into memory."""
        start = time()
        if mode == "pos":
            with open(self.configuration.paths.spectral_db_pos, "rb") as f:
                self.spectral_db: list[Spectrum] = pickle.load(f)
        elif mode == "neg":
            with open(self.configuration.paths.spectral_db_neg, "rb") as f:
                self.spectral_db: list[Spectrum] = pickle.load(f)
        else:
            raise ValueError(f"Invalid mode '{mode}' for loading spectral database")
        self.logger.debug(f"Loaded {mode} mode spectral database in {time() - start:.2f} seconds")


class ISDBEnricher(Enricher):
    """Enricher that adds ISDB information to the analysis."""

    def __init__(
        self, configuration: ISDBEnricherConfig, logger: Logger
    ):
        """Initializes the enricher."""
        
        if not isinstance(configuration, ISDBEnricherConfig):
            raise TypeError(
                f"Expected configuration of type ISDBEnricherConfig, got {type(configuration)}"
            )
        if not isinstance(logger, Logger):
            raise TypeError(f"Expected logger of type logging.Logger, got {type(logger)}")
        self.configuration = configuration
        self.logger = logger

        self.logger.info("Loading Databases")
        self.databases = DBLoader(configuration=configuration, logger=logger) # use the db_loader to get db paths to ensure they are downloaded
        
        start = time()
        self.databases.load_taxonomical_databases()
        self.logger.debug("Taxonomical databases loaded in %.2f seconds", time() - start)
        self.databases.load_spectral_databases(mode="pos") # TODO: add mode param to config
        self.logger.debug("Spectral databases loaded in %.2f seconds", time() - start)
        
        self.logger.info(
            "Converting Taxonomical Database metadata DataFrame to Lotus objects"
        )
        self._initialize_lotus_objects()

        # Liberate memory by deleting the original dataframes and keeping only the Lotus objects and spectral database in memory
        # (Can't be bothered to wait for the garbage collector)
        del self.databases.lotus_metadata, self.databases.lotus_metadata_pathways, 
        self.databases.lotus_metadata_superclasses, self.databases.lotus_metadata_classes

        # TODO: Could be put elsewhere
        if not isinstance(self.databases.spectral_db, list):
            raise TypeError(f"Expected spectral_db to be a list, got {type(self.databases.spectral_db)}")
        if not all(isinstance(spectrum, Spectrum) for spectrum in self.databases.spectral_db):
            raise TypeError("Expected all entries in spectral_db to be of type matchms.Spectrum")
        if not all(spectrum.get("compound_name") is not None for spectrum in self.databases.spectral_db[:10]):
            raise ValueError("Expected all spectra in spectral_db to have 'compound_name' metadata for short inchikey matching")

        self.logger.info("Adding Lotus entries to spectral database")
        self._link_lotus_to_spectra()
        self.logger.debug(
            "Added Lotus entries to spectral database in %.2f seconds", time() - start
        )

        self.logger.info("ISDB Enricher initialized successfully")

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "ISDB Enricher"
    
    def _link_lotus_to_spectra(self) -> None:
        """Link Lotus entries to spectral database entries by short inchikey.
        
        For each spectrum, finds all Lotus entries with matching short inchikey
        using binary search and attaches them as metadata.
        """

        start = time()
        for spectrum in tqdm(
            self.databases.spectral_db,
            desc="Adding Lotus entries to spectral database",
            dynamic_ncols=True,
            leave=False,
        ):
            spectrum_short_inchikey = spectrum.get("compound_name")
            (found, smallest_idx) = binary_search_by_key(
                key=spectrum_short_inchikey,
                array=self.lotus_objects,
                key_func=lambda x: x.short_inchikey,
            )

            if not found:
                continue

            # Since we may have landed exactly in the middle of an array of short inchikeys
            # with the same value, we need to identify the smallest index of the slice of
            # short inchikeys with the same value.
            while (
                smallest_idx > 0
                and self.lotus_objects[smallest_idx - 1].short_inchikey
                == spectrum_short_inchikey
            ):
                smallest_idx -= 1

            largest_idx = smallest_idx

            while (
                largest_idx < len(self.lotus_objects)
                and self.lotus_objects[largest_idx].short_inchikey == spectrum_short_inchikey
            ):
                largest_idx += 1

            spectrum.set("lotus_entries", self.lotus_objects[smallest_idx:largest_idx])

            self.logger.debug(f"Linked lotus to spectra in {time() - start:.2f} seconds")

    
    def _initialize_lotus_objects(self) -> None:
        """Initializes the Lotus objects from the metadata dataframe."""

        start = time()
        structure_smiles_column_number: int = self.databases.lotus_metadata.columns.get_loc(
            "structure_smiles"
        )
        Lotus.setup_lotus_columns(list(self.databases.lotus_metadata.columns))
        self.logger.debug(f"Lotus columns set up in %.2f seconds", time() - start)
        self.logger.debug(f"Lotus columns: {Lotus._columns}")
        self.logger.debug(f"Converting {len(self.databases.lotus_metadata)} Lotus entries to Lotus objects")
        
        # Create lookup dictionaries for pathways, superclasses, and classes
        start = time()
        pathways_lookup = self.databases.lotus_metadata_pathways.T.to_dict('series')
        superclasses_lookup = self.databases.lotus_metadata_superclasses.T.to_dict('series')
        classes_lookup = self.databases.lotus_metadata_classes.T.to_dict('series')
        self.logger.debug(f"Built lookup dictionaries in {time() - start:.2f} seconds")

        start = time()
        # Create the Lotus objects. 
        # TODO: Will be done in initialization step of the workflow in the future.
        # TODO: Could be further optimized by parallelizing the creation of Lotus objects
        self.lotus_objects: list[Lotus] = [
            Lotus.from_pandas_series(
                list(row),
                pathways=pathways_lookup[row[structure_smiles_column_number]],
                superclasses=superclasses_lookup[row[structure_smiles_column_number]],
                classes=classes_lookup[row[structure_smiles_column_number]],
            )
            for row in tqdm(
                self.databases.lotus_metadata.values,
                desc="Creating Lotus objects",
                leave=False,
                dynamic_ncols=True,
            )
        ]
        self.logger.debug(
            "Converted Taxonomical Database metadata DataFrame to Lotus objects in %.2f seconds",
            time() - start,
        )

        self.logger.debug("Sorting Lotus entries by short inchikey")
        start = time()
        # We sort lotus by the short inchikey so that we can do binary search
        # of the spectral db inchikeys and align the two databases.
        self.lotus_objects = sorted(self.lotus_objects, key=lambda x: x.short_inchikey)
        self.logger.debug(
            "Sorted Lotus entries by short inchikey in %.2f seconds", time() - start
        )

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
            spectra_chunk: list[AnnotatedSpectrum] = analysis.tandem_mass_spectra[
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

            total_combined_similarity = np.sum(combined_similarities)

            if total_combined_similarity > 0:
                # We normalize the combined similarity scores
                combined_similarities /= total_combined_similarity

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
    


if __name__ == "__main__":

    logger = logging.getLogger("DBLoader")
    logging.basicConfig(level=logging.DEBUG)
    paths = Paths(
        taxo_db_metadata="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_metadata.csv",
        spectral_db_pos="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/spectral_db_pos.pkl",
        taxo_db_pathways="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_pathways.csv",
        taxo_db_superclasses="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_superclasses.csv",
        taxo_db_classes="/home/llegregam/git_projects/enpkg_full/enpkg/monolith/enrichers/test_isdb/taxo_db_classes.csv"
    )
    urls = Urls(
        taxo_db_metadata="https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz",
        taxo_db_pathways="https://zenodo.org/records/13951644/files/pathways.csv.gz?download=1",
        taxo_db_superclasses="https://zenodo.org/records/13951644/files/superclasses.csv.gz?download=1",
        taxo_db_classes="https://zenodo.org/records/13951644/files/classes.csv.gz?download=1",
        spectral_db_pos="https://zenodo.org/records/8287341/files/isdb_pos_cleaned.pkl"
    )

    config = ISDBEnricherConfig(
        general_params=GeneralParams(
            redownload_if_exists=False
        ),
        urls = urls,
        paths = paths
    )
    print("Config=", config)

    enricher = ISDBEnricher(configuration=config, logger=logger)
