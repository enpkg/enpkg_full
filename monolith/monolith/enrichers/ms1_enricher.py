"""Submodule for the MS1 level enricher, which adds the Adducts to a given batch and computes its LPA scores."""

from time import time
from typing import List, Optional
from logging import Logger
import pandas as pd
import numpy as np
from downloaders import BaseDownloader

from tqdm.auto import tqdm

from typeguard import typechecked

from monolith.enrichers.enricher import Enricher
from monolith.data import Analysis
from monolith.enrichers.adducts import POSITIVE_RECIPES, NEGATIVE_RECIPES
from monolith.data import MS1EnricherConfig
from monolith.data.lotus_class import (
    Lotus,
)
from monolith.data.otl_class import Match
from monolith.data import ChemicalAdduct
from monolith.utils import binary_search_by_key, label_propagation_algorithm


class MS1Enricher(Enricher):
    """Enricher that adds MS1 information to the analysis."""

    @typechecked
    def __init__(
        self, configuration: MS1EnricherConfig, polarity: bool, logger: Logger
    ):
        """Initializes the enricher."""
        assert isinstance(configuration, MS1EnricherConfig)
        assert isinstance(polarity, bool)

        self.configuration = configuration
        self.polarity = polarity
        downloader = BaseDownloader()
        downloader.download(
            [
                self.configuration.taxo_db_metadata_url,
                self.configuration.taxo_db_pathways_url,
                self.configuration.taxo_db_superclasses_url,
                self.configuration.taxo_db_classes_url,
            ],
            [
                self.configuration.taxo_db_metadata_path,
                self.configuration.taxo_db_pathways_path,
                self.configuration.taxo_db_superclasses_path,
                self.configuration.taxo_db_classes_path,
            ],
        )

        logger.info("Loading Taxonomical Database metadata")
        start = time()
        lotus_metadata: pd.DataFrame = pd.read_csv(
            self.configuration.taxo_db_metadata_path, low_memory=False
        )
        lotus_metadata_pathways: pd.DataFrame = pd.read_csv(
            self.configuration.taxo_db_pathways_path,
            index_col=0,
        )
        self._number_of_pathways = lotus_metadata_pathways.shape[1]
        self._pathways = lotus_metadata_pathways.columns
        lotus_metadata_superclasses: pd.DataFrame = pd.read_csv(
            self.configuration.taxo_db_superclasses_path,
            index_col=0,
        )
        self._number_of_superclasses = lotus_metadata_superclasses.shape[1]
        self._superclasses = lotus_metadata_superclasses.columns
        lotus_metadata_classes: pd.DataFrame = pd.read_csv(
            self.configuration.taxo_db_classes_path,
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
        lotus_grouped_by_structure_molecular_formula: List[List[Lotus]] = [
            [
                Lotus.from_pandas_series(
                    list(row),
                    pathways=lotus_metadata_pathways.loc[
                        row[structure_smiles_column_number]
                    ],
                    superclasses=lotus_metadata_superclasses.loc[
                        row[structure_smiles_column_number]
                    ],
                    classes=lotus_metadata_classes.loc[
                        row[structure_smiles_column_number]
                    ],
                )
                for row in group.values
            ]
            for (_, group) in lotus_metadata.groupby(by=["structure_molecular_formula"])
        ]
        logger.info(
            "Converted Taxonomical Database metadata DataFrame to Lotus objects in %.2f seconds",
            time() - start,
        )

        logger.info("Creating adducts")
        start = time()
        self._adducts: List[ChemicalAdduct] = (
            [
                ChemicalAdduct(
                    lotus=lotus_group,
                    recipe=recipe,
                )
                for lotus_group in lotus_grouped_by_structure_molecular_formula
                for recipe in POSITIVE_RECIPES
            ]
            if polarity
            else [
                ChemicalAdduct(
                    lotus=lotus_group,
                    recipe=recipe,
                )
                for lotus_group in lotus_grouped_by_structure_molecular_formula
                for recipe in NEGATIVE_RECIPES
            ]
        )

        logger.info(
            "Created %d adducts in %.2f seconds",
            len(self._adducts),
            time() - start,
        )

        start = time()

        # We sort the adducts by the 'adduct_mass' key so that when
        # we match the precursor mass with the adducts, we can do so
        # via binary search.

        self._adducts = sorted(self._adducts, key=lambda x: x.adduct_mass)

        logger.info(
            "Sorted %d adducts by exact mass in %.2f seconds",
            len(self._adducts),
            time() - start,
        )

    def name(self) -> str:
        """Returns the name of the enricher."""
        return "MS1 Enricher"

    def enrich(self, analysis: Analysis) -> Analysis:
        """Adds MS1 information to the analysis."""

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

        for i, spectrum in tqdm(
            enumerate(analysis.tandem_mass_spectra),
            leave=False,
            total=analysis.number_of_spectra,
            desc="Filtering precursor adducts",
            dynamic_ncols=True,
        ):
            lower_bound = (
                spectrum.precursor_mz
                - spectrum.precursor_mz * self.configuration.tolerance
            )
            upper_bound = (
                spectrum.precursor_mz
                + spectrum.precursor_mz * self.configuration.tolerance
            )

            # Find the lower bound by exploring the sorted adducts via binary search
            (_, lower_bound_index) = binary_search_by_key(
                key=lower_bound,
                array=self._adducts,
                key_func=lambda adduct: adduct.adduct_mass,
            )

            # Find the upper bound by linear search starting from the identified lower
            # bound index and iterating up until we wncounter an adduct with an exact mass
            # greater than the upper bound
            upper_bound_index = lower_bound_index

            while upper_bound > self._adducts[upper_bound_index].adduct_mass:
                upper_bound_index += 1

                if upper_bound_index == len(self._adducts):
                    break

            spectrum.set_ms1_annotations(
                self._adducts[lower_bound_index:upper_bound_index]
            )

        best_ott_match: Optional[Match] = analysis.best_ott_match

        for i, spectrum in tqdm(
            enumerate(analysis.tandem_mass_spectra),
            leave=False,
            total=analysis.number_of_spectra,
            desc="Computing MS1 NPC scores",
            dynamic_ncols=True,
        ):
            # If the spectrum has no adducts, we cannot make assumptions regarding its scores,
            # and therefore we give uniform scores to all pathways, superclasses, and classes.
            if not spectrum.has_ms1_annotations():
                pathway_features[i] = np.zeros(
                    shape=(self._number_of_pathways,),
                )
                superclass_features[i] = np.zeros(
                    shape=(self._number_of_superclasses,),
                )
                class_features[i] = np.zeros(
                    shape=(self._number_of_classes,),
                )
                continue

            # Now that we have determined the adducts potentially associated with this
            # spectrum, we can populate the associated features with the adducts' pathway,
            # superclass, and class annotations, weighted by the adduct's normalized
            # taxonomical similarity score.

            # First, we compute the maximal normalized taxonomical similarity score for
            # each adducts, if we do have a known sample taxonomy match.
            if best_ott_match is not None:
                taxonomical_similarities: np.ndarray = np.fromiter(
                    (
                        adduct.maximal_normalized_taxonomical_similarity(best_ott_match)
                        for adduct in spectrum.ms1_annotations
                    ),
                    dtype=np.float32,
                )
            else:
                taxonomical_similarities: np.ndarray = np.ones(
                    shape=(len(spectrum.ms1_annotations),), dtype=np.float32
                )

            taxonomical_similarities /= np.sum(taxonomical_similarities)

            for taxonomical_similarity, adduct in zip(
                taxonomical_similarities, spectrum.ms1_annotations
            ):
                pathway_features[i] += (
                    taxonomical_similarity * adduct.get_hammer_pathway_scores()
                )

                superclass_features[i] += (
                    taxonomical_similarity * adduct.get_hammer_superclass_scores()
                )

                class_features[i] += (
                    taxonomical_similarity * adduct.get_hammer_class_scores()
                )

        # THIS SHOULD BE DELETED AFTERWARDS! DO NOT KEEP THIS!

        pathway = pd.DataFrame(pathway_features, columns=self._pathways)
        pathway.to_csv("downloads/before_lpa_ms1_pathway.csv", index=False)
        superclass = pd.DataFrame(superclass_features, columns=self._superclasses)
        superclass.to_csv("downloads/before_lpa_ms1_superclass.csv", index=False)
        classes = pd.DataFrame(class_features, columns=self._classes)
        classes.to_csv("downloads/before_lpa_ms1_class.csv", index=False)

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
            spectrum.set_ms1_hammer_pathway_scores(propagated_pathway[i])
            spectrum.set_ms1_hammer_superclass_scores(propagated_superclass[i])
            spectrum.set_ms1_hammer_class_scores(propagated_class[i])

        # THIS SHOULD BE DELETED AFTERWARDS! DO NOT KEEP THIS!

        pathway = pd.DataFrame(propagated_pathway, columns=self._pathways)
        pathway.to_csv("downloads/ms1_pathway.csv", index=False)
        superclass = pd.DataFrame(propagated_superclass, columns=self._superclasses)
        superclass.to_csv("downloads/ms1_superclass.csv", index=False)
        classes = pd.DataFrame(propagated_class, columns=self._classes)
        classes.to_csv("downloads/ms1_class.csv", index=False)

        return analysis
