"""Submodule with data classes for the Sirius analysis of mass spectrometry data."""

from enpkg.monolith.data.sirius_data_classes.sirius_chemical_annotation import (
    SiriusChemicalAnnotation,
)
from enpkg.monolith.data.sirius_data_classes.sirius_configuration_class import (
    SiriusEnricherConfig,
)

__all__ = ["SiriusChemicalAnnotation", "SiriusEnricherConfig"]
