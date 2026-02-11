"""Submodule providing the configuration classes for the ISDB enricher."""

from enpkg.monolith.data.isdb_data_classes.isdb_configuration_class import ISDBEnricherConfig
from enpkg.monolith.data.isdb_data_classes.isdb_chemical_annotation import (
    ISDBChemicalAnnotation,
)

__all__ = [
    "ISDBEnricherConfig",
    "ISDBChemicalAnnotation",
]
