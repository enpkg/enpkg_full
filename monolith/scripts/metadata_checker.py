"""Script to check which entries of the Taxonomical information scoring paper benchmark set are in LOTUS"""

from downloaders import BaseDownloader
import pandas as pd

BENCHMARK_DATASET_URL = "https://osf.io/download/ye4gx/"


def overlap_with_lotus() -> float:
    """Returns the rate of overlap between the benchmark dataset and LOTUS"""
    downloader = BaseDownloader()
    downloader.download(BENCHMARK_DATASET_URL, "downloads/benchmark.tsv")

    lotus = pd.read_csv("downloads/taxo_db_metadata.csv")
    benchmark = pd.read_csv("downloads/benchmark.tsv", sep="\t")

    lotus_short_inchikeys = {inchikey[:14] for inchikey in lotus["structure_inchikey"]}

    benchmark_short_inchikeys = {inchikey[:14] for inchikey in benchmark["InChIKey"]}

    return (
        len(lotus_short_inchikeys.intersection(benchmark_short_inchikeys))
        / len(benchmark_short_inchikeys)
        * 100.0
    )


if __name__ == "__main__":
    print(f"{overlap_with_lotus()}% of the benchmark entries appear in LOTUS")
