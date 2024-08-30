""" This module contains the Batch class. """

from typing import List
import matchms
from matchms.importing import load_from_mgf
from matchms.filtering import add_precursor_mz, require_minimum_number_of_peaks
import pandas as pd
import os

from monolith.data.analysis_class import Analysis


class Batch:
    """This is a class for the Batch class.

    Attributes:
    - analyses: List[Analysis], a list of Analysis objects
    - lcms_method_params: str, the parameters of the LCMS method
    - lcms_processing_params_path: str, the path to the LCMS processing parameters

    """

    def __init__(
        self,
        metadata_path: str,
        methods_directory: str = "methods",
        mzml_directory: str = "mzml",
        treated_data_directory: str = "treated_data",
    ):
        """Load an analysis from a metadata file."""
        metadata = pd.read_csv(metadata_path, sep="\t")
        analyses = []
        tandem_mass_spectra_path_pattern = os.path.join(
            treated_data_directory, "{sample_filename}.mgf"
        )
        feature_quantification_table_path_pattern = os.path.join(
            treated_data_directory,
            "{sample_filename}.mzML_eics_sm_r_deiso_filtered_peak_quant.csv",
        )

        lcms_method_params_path = os.path.join(
            methods_directory, "lcms_method_params.txt"
        )

        with open(lcms_method_params_path, "r", encoding="utf-8") as f:
            self._lcms_method_params = f.read()

        self._lcms_processing_params_path = os.path.join(
            methods_directory, "lcms_processing_params.mzbatch"
        )

        for i, row in metadata.iterrows():
            sample_filename = row["sample_filename"]
            assert sample_filename.endswith(
                ".mzML"
            ), "sample_filename must end with .mzML"
            sample_filename_no_ext = sample_filename.rsplit(".", 1)[0]

            tandem_mass_spectra_path = tandem_mass_spectra_path_pattern.format(
                sample_filename=sample_filename_no_ext
            )

            tandem_mass_spectra = [
                add_precursor_mz(spectrum)
                for spectrum in load_from_mgf(tandem_mass_spectra_path)
                if require_minimum_number_of_peaks(spectrum, n_required=1)
            ]

            feature_quantification_table_path = (
                feature_quantification_table_path_pattern.format(
                    sample_filename=sample_filename_no_ext
                )
            )

            feature_quantification_table = pd.read_csv(
                feature_quantification_table_path
            )

            # We only want the following columns from the feature quantification table

            feature_quantification_table = feature_quantification_table[
                [
                    "row ID",
                    "row m/z",
                    "row retention time",
                    f"{sample_filename} Peak height",
                ]
            ]

            # We rename the variable column '{sample_filename} Peak height' to 'Peak height'

            feature_quantification_table.rename(
                columns={f"{sample_filename} Peak height": "Peak height"}, inplace=True
            )

            assert feature_quantification_table.shape[0] == len(
                tandem_mass_spectra
            ), "The number of features and the number of spectra must be the same"

            # We check that the row ID column is both dense and sorted.

            assert feature_quantification_table[
                "row ID"
            ].is_monotonic_increasing, "The row ID column must be sorted"
            assert feature_quantification_table[
                "row ID"
            ].is_unique, "The row ID column must be unique"

            analysis = Analysis(
                metadata=row,
                tandem_mass_spectra=tandem_mass_spectra,
                features_quantification_table=feature_quantification_table,
            )
            analyses.append(analysis)

        self._analyses = analyses

    @property
    def number_of_analyses(self):
        """Return the number of analyses."""
        return len(self._analyses)

    @property
    def analyses(self):
        """Return the list of analyses."""
        return self._analyses
