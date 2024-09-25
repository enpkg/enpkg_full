"""Submodule for the MS1 level enricher, which adds the Adducts to a given batch and computes its LPA scores."""

from time import time
from typing import List
from logging import Logger
import pandas as pd
import numpy as np
from downloaders import BaseDownloader

from tqdm.auto import tqdm
from monolith.enrichers.enricher import Enricher
from monolith.data import Analysis
from monolith.enrichers.adducts import POSITIVE_RECIPES, NEGATIVE_RECIPES
from monolith.data import MS1EnricherConfig
from monolith.data.lotus_class import (
    Lotus,
    NPC_PATHWAYS,
    NPC_SUPERCLASSES,
    NPC_CLASSES,
    NUMBER_OF_NPC_CLASSES,
    NUMBER_OF_NPC_PATHWAYS,
    NUMBER_OF_NPC_SUPERCLASSES,
)
from monolith.data import ChemicalAdduct
from monolith.utils import binary_search_by_key, label_propagation_algorithm


class MS1Enricher(Enricher):
    """Enricher that adds MS1 information to the analysis."""

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
            self.configuration.taxo_db_metadata_url,
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
        lotus_grouped_by_structure_molecular_formula: List[List[Lotus]] = [
            [Lotus.from_pandas_series(row) for row in group.values]
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
            (analysis.number_of_spectra, NUMBER_OF_NPC_PATHWAYS), dtype=np.float32
        )
        superclass_features = np.zeros(
            (analysis.number_of_spectra, NUMBER_OF_NPC_SUPERCLASSES),
            dtype=np.float32,
        )
        class_features = np.zeros(
            (analysis.number_of_spectra, NUMBER_OF_NPC_CLASSES), dtype=np.float32
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
                    shape=(NUMBER_OF_NPC_PATHWAYS,),
                )
                superclass_features[i] = np.zeros(
                    shape=(NUMBER_OF_NPC_SUPERCLASSES,),
                )
                class_features[i] = np.zeros(
                    shape=(NUMBER_OF_NPC_CLASSES,),
                )
                continue

            # Now that we have determined the adducts potentially associated with this
            # spectrum, we can populate the associated features with the adducts' pathway,
            # superclass, and class annotations, weighted by the adduct's normalized
            # taxonomical similarity score.
            for adduct in spectrum.ms1_annotations:
                pathway_features[i] += adduct.get_npc_pathway_scores(
                    analysis.best_ott_match
                )

                superclass_features[i] += adduct.get_npc_superclass_scores(
                    analysis.best_ott_match
                )

                class_features[i] += adduct.get_npc_class_scores(
                    analysis.best_ott_match
                )

            # And we normalize the scores by the number of adducts
            pathway_features[i] /= len(spectrum.ms1_annotations)
            superclass_features[i] /= len(spectrum.ms1_annotations)
            class_features[i] /= len(spectrum.ms1_annotations)

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
            spectrum.set_ms1_npc_pathway_scores(propagated_pathway[i])
            spectrum.set_ms1_npc_superclass_scores(propagated_superclass[i])
            spectrum.set_ms1_npc_class_scores(propagated_class[i])

        # THIS SHOULD BE DELETED AFTERWARDS! DO NOT KEEP THIS!

        pathway = pd.DataFrame(propagated_pathway, columns=NPC_PATHWAYS)
        pathway.to_csv("downloads/ms1_pathway.csv", index=False)
        superclass = pd.DataFrame(propagated_superclass, columns=NPC_SUPERCLASSES)
        superclass.to_csv("downloads/ms1_superclass.csv", index=False)
        classes = pd.DataFrame(propagated_class, columns=NPC_CLASSES)
        classes.to_csv("downloads/ms1_class.csv", index=False)

        return analysis
