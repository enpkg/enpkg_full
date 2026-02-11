""" This module contains the Batch class. """

import os
from matchms.filtering import default_filters
from matchms.filtering import normalize_intensities
from matchms.filtering import select_by_intensity
from matchms.filtering import select_by_mz
from matchms import Spectrum
from matchms.importing import load_from_mgf
from matchms.filtering import require_minimum_number_of_peaks
import pandas as pd

from monolith.data.analysis_class import Analysis


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


class Batch:
    """This is a class for the Batch class.

    Attributes:
    - analyses: list[Analysis], a list of Analysis objects
    - lcms_method_params: str, the parameters of the LCMS method
    - lcms_processing_params_path: str, the path to the LCMS processing parameters

    """

    def __init__(
        self,
        metadata_path: str,
        methods_directory: str = "methods",
        mzml_directory: str = "mzml",
        treated_data_directory: str = "treated_data",
        minimum_number_of_peaks: int = 1,
    ):
        """Load an analysis from a metadata file."""
        metadata = pd.read_csv(metadata_path, sep="\t")
        analyses = []
        tandem_mass_spectra_path_pattern = os.path.join(
            treated_data_directory, "{sample_filename}.mgf"
        )
        tandem_mass_spectra_for_sirius_path_pattern = os.path.join(
            treated_data_directory, "{sample_filename}_sirius.mgf"
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

        for _, row in metadata.iterrows():
            sample_filename = row["sample_filename"]
            assert sample_filename.endswith(
                ".mzML"
            ), "sample_filename must end with .mzML"
            sample_filename_no_ext = sample_filename.rsplit(".", 1)[0]

            tandem_mass_spectra_path = tandem_mass_spectra_path_pattern.format(
                sample_filename=sample_filename_no_ext
            )

            tandem_mass_spectra_for_sirius_path = tandem_mass_spectra_for_sirius_path_pattern.format(
                sample_filename=sample_filename_no_ext
            )

            tandem_mass_spectra = [
                peak_processing(spectrum)
                for spectrum in load_from_mgf(tandem_mass_spectra_path)
                if require_minimum_number_of_peaks(spectrum, n_required=minimum_number_of_peaks)
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
                tandem_mass_spectra_for_sirius_path=tandem_mass_spectra_for_sirius_path,
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
