"""Script to compare similarity metrics for spectra and their correlation with SMILES similarity."""

from typing import Optional, Type
import os
from multiprocessing import cpu_count, Pool
from argparse import ArgumentParser, Namespace
from downloaders import BaseDownloader
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr, kendalltau
from matchms.importing import load_from_mgf
from matchms.exporting import save_as_mgf
from matchms.filtering import normalize_intensities, default_filters
from matchms import Spectrum
from matchms.similarity import (
    CosineGreedy,
    NeutralLossesCosine,
    ModifiedCosine,
)
from tqdm.auto import tqdm, trange
from skfp.bases import BaseFingerprintTransformer
from skfp.fingerprints.ecfp import ECFPFingerprint
from skfp.fingerprints.avalon import AvalonFingerprint
from skfp.fingerprints.layered import LayeredFingerprint
from skfp.fingerprints.rdkit_fp import RDKitFingerprint
from numba import njit, prange


@njit(parallel=True)
def smiles_similarities(rows: np.ndarray, columns: np.ndarray) -> np.ndarray:
    """Calculate the similarities between the rows and columns of the fingerprints."""
    similarity = np.zeros(
        (
            rows.shape[0],
            columns.shape[0],
        ),
        dtype=np.float32,
    )
    for i in prange(rows.shape[0]):  # pylint: disable=not-an-iterable
        row = rows[i]
        for j in range(columns.shape[0]):
            column = columns[j]
            for k in range(row.shape[0]):
                if row[k] == column[k]:
                    similarity[i, j] += 1
            similarity[i, j] /= row.shape[0]
    return similarity


def retrieve_gnps(verbose: bool) -> list[Spectrum]:
    """Retrieve the GNPS dataset."""

    if os.path.exists("lotus_spectra.mgf"):
        return list(load_from_mgf("lotus_spectra.mgf"))

    downloader = BaseDownloader(process_number=1, auto_extract=False)
    downloader.download(
        [
            "https://external.gnps2.org/processed_gnps_data/gnps_cleaned.mgf",
            "https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz",
        ],
        ["gnps_cleaned.mgf", "lotus_metadata.csv.gz"],
    )

    lotus_df = pd.read_csv("lotus_metadata.csv.gz", low_memory=False)

    lotus_smiles = set(lotus_df["structure_smiles"].tolist())
    spectra_in_lotus: list[Spectrum] = []
    for spectrum in tqdm(
        load_from_mgf("gnps_cleaned.mgf"),
        desc="Loading spectra",
        unit="spectrum",
        dynamic_ncols=True,
        leave=False,
        disable=not verbose,
    ):
        smile: Optional[str] = spectrum.get("smiles")
        if smile is None:
            continue
        if smile in lotus_smiles:
            spectra_in_lotus.append(normalize_intensities(default_filters(spectrum)))

    save_as_mgf(spectra_in_lotus, "lotus_spectra.mgf")

    return spectra_in_lotus


def calculate_fingerprints(
    spectra: list[Spectrum], fingerprint_class: Type[BaseFingerprintTransformer]
) -> np.ndarray:
    """Calculate the fingerprints for the spectra."""
    fingerprint = fingerprint_class(n_jobs=cpu_count(), verbose=1)
    fingerprints = fingerprint.fit_transform(
        [spectrum.get("smiles") for spectrum in spectra]
    )

    return fingerprints


def compute_similarity(args) -> np.ndarray:
    """Compute the similarity between the row spectrum and the column spectra."""
    similarity_class, row_spectra, column_spectra = args
    similarity = similarity_class()
    similarity_scores = np.zeros(
        (
            len(row_spectra),
            len(column_spectra),
        ),
        dtype=np.float32,
    )
    for i, row_spectrum in enumerate(row_spectra):
        for j, column_spectrum in enumerate(column_spectra):
            score, _ = similarity.pair(row_spectrum, column_spectrum)[()]
            similarity_scores[i, j] = score
    return similarity_scores


def determine_correlations(
    spectra: list[Spectrum],
    args: Namespace,
) -> float:
    """Determine the correlation between the similarity scores and the SMILES similarity."""
    similarities: list[dict] = []

    fingerprints: dict[str, np.ndarray] = {
        fingerprint_class.__name__: calculate_fingerprints(spectra, fingerprint_class)
        for fingerprint_class in tqdm(
            (ECFPFingerprint, AvalonFingerprint, RDKitFingerprint, LayeredFingerprint),
            desc="Calculating fingerprints",
            leave=False,
            unit="fingerprint",
            disable=not args.verbose,
            dynamic_ncols=True,
        )
    }

    for _ in trange(
        args.iterations,
        desc="Iteration",
        leave=False,
        dynamic_ncols=True,
        disable=not args.verbose,
        unit="iteration",
    ):
        # Since we can't actually compute the similarities across the full dataset,
        # we subsample the spectra to calculate the similarity.
        row_indices: np.ndarray = np.random.choice(
            np.arange(len(spectra)), size=args.spectra, replace=False
        )
        columns_indices: np.ndarray = np.random.choice(
            np.arange(len(spectra)), size=args.spectra, replace=False
        )
        row_spectra = [spectra[i] for i in row_indices]
        column_spectra = [spectra[i] for i in columns_indices]

        spectra_similarities: list[tuple[str, np.ndarray]] = []

        for similarity_class in tqdm(
            (CosineGreedy, NeutralLossesCosine, ModifiedCosine),
            desc="Calculating similarity",
            leave=False,
            unit="similarity",
            dynamic_ncols=True,
            disable=not args.verbose,
        ):
            spectra_similarity: np.ndarray = np.zeros(
                (
                    len(row_spectra),
                    len(column_spectra),
                ),
                dtype=np.float32,
            )

            with Pool(cpu_count()) as pool:
                chunk_size = len(row_spectra) // cpu_count()
                tasks = (
                    (
                        similarity_class,
                        row_spectra[
                            chunk_number * chunk_size : (chunk_number + 1) * chunk_size
                        ],
                        column_spectra,
                    )
                    for chunk_number in range(cpu_count())
                )
                for i, similarities_chunk in enumerate(
                    tqdm(
                        pool.imap(compute_similarity, tasks),
                        desc="Calculating similarity",
                        leave=False,
                        dynamic_ncols=True,
                        disable=not args.verbose,
                        unit="spectrum",
                        total=cpu_count(),
                    )
                ):
                    spectra_similarity[i * chunk_size : (i + 1) * chunk_size] = (
                        similarities_chunk
                    )

            spectra_similarities.append((similarity_class.__name__, spectra_similarity))

        for fingerprint_name, fingerprints in tqdm(
            fingerprints.items(),
            desc="Calculating fingerprint correlations",
            leave=False,
            unit="fingerprint",
            disable=not args.verbose,
            dynamic_ncols=True,
        ):
            smiles_similarity: np.ndarray = smiles_similarities(
                fingerprints[row_indices], fingerprints[columns_indices]
            )

            for spectra_similarity_name, spectra_similarity in spectra_similarities:

                for correlation_method in tqdm(
                    (pearsonr, spearmanr, kendalltau),
                    desc="Calculating correlation",
                    leave=False,
                    unit="correlation",
                    dynamic_ncols=True,
                    disable=not args.verbose,
                ):
                    correlation, p_value = correlation_method(
                        smiles_similarity.flatten(), spectra_similarity.flatten()
                    )

                    similarities.append(
                        {
                            "smiles_fingerprint": fingerprint_name,
                            "spectra_similarity": spectra_similarity_name,
                            "correlation_method": correlation_method.__name__,
                            "correlation": correlation,
                            "p_value": p_value,
                        }
                    )

    return pd.DataFrame(similarities)


def measure_correlations(
    args: Namespace,
) -> None:
    """Measure the correlations between similarity metrics and SMILES similarity."""
    lotus_spectra = retrieve_gnps(args.verbose)
    correlations: pd.DataFrame = determine_correlations(lotus_spectra, args)
    correlations.to_csv(args.output, index=False)


def build_parser() -> ArgumentParser:
    """Build the argument parser."""
    parser = ArgumentParser()
    parser.add_argument(
        "--n_jobs",
        type=int,
        default=cpu_count(),
        help="The number of jobs to use for the calculation.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Whether to print verbose output.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="The number of iterations to perform.",
    )
    parser.add_argument(
        "--spectra",
        type=int,
        default=10_000,
        help="The number of spectra to use for the calculation.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cosine_correlations.csv",
        help="The output file to save the results.",
    )
    return parser


if __name__ == "__main__":
    measure_correlations(build_parser().parse_args())
