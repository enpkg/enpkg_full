# A short experiment on Cosine Correlations

Compares the correlation between different cosine similarity metrics and the Jaccard similarity of different molecular fingerprints.

## Experiment

This experiment goal is to determine whether there is correlation, of which type and how strong, between the cosine similarity of different spectra similarity metrics and the Jaccard similarity of different molecular fingerprints, with a focus on Natural Products as provided from the LOTUS dataset.

### Data

We retrieve the entries from the LOTUS dataset from [zenodo](https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz), which provides descriptions for `792_364` natural products, and the spectra from [GNPS Cleaned MGF dataset](https://external.gnps2.org/processed_gnps_data/gnps_cleaned.mgf), which contains `722_864` spectra. We then filter the spectra to only include the ones from the LOTUS dataset, leaving us with `250_300` spectra. The spectra are then filtered and normalized using the matchms library standard pipeline.

### Considered spectra similarites

For all of these spectra similarities, we use the [matchms library](https://matchms.readthedocs.io/en/latest/index.html) to compute the similarity between the spectra.

We consider the [`CosineGreedy`](https://matchms.readthedocs.io/en/latest/api/matchms.similarity.CosineGreedy.html), [`NeutralLossesCosine`](https://matchms.readthedocs.io/en/latest/api/matchms.similarity.NeutralLossesCosine.html) and [`ModifiedCosine`](https://matchms.readthedocs.io/en/latest/api/matchms.similarity.ModifiedCosine.html) as the similarity metrics for the spectra. All of the smiles are considered in canonical form.

In an earlier iteration, we also considered the [`CosineHungarian`](https://matchms.readthedocs.io/en/latest/api/matchms.similarity.CosineHungarian.html) metric, but it was discarded due to its excessive memory and time requirements (in practice, it completed just 800 spectra tuples in 24 hours, using 64 threads on a machine with 32 cores and 64 threads).

### Considered fingerprints

For all of the fingerprints, we use the [scikit-fingerprints library](https://github.com/scikit-fingerprints/scikit-fingerprints) which in turn extensively uses [RDKit](https://www.rdkit.org/).

We consider the Extended Connectivity Fingerprint (also known as Morgan fingerprint), Avalon Fingerprint, RDKit Fingerprint and the Layered Fingerprint.

The Extended Connectivity Fingerprint is a hashed fingerprint, where fragments are computed based on circular substructures around each atom.
The Avalon Fingerprint is a hashed fingerprint, where fragments are computed based on atom environments. The fingerprint is based on multiple features, including atom types, bond types, rings and paths.
The RDKit Fingerprint is a hashed fingerprint, where fragments are created from small subgraphs on the molecular graph.
Finally, the Layered Fingerprint is a hashed fingerprint, where fragments are created from the molecular graph, with the addition of layers of information. It is a derivative of the RDKit Fingerprint.

All of these fingerprints produce a binary vector of length `2048`.

### Correlations

For all of the correlations, we use the [scipy library](https://www.scipy.org/). We consider Spearman’s correlation, Pearson’s correlation and Kendall’s tau correlation.

Spearman’s correlation measures the monotonic relationship between two variables, based on their rank order rather than their actual values.
Pearson’s correlation measures the linear relationship between two variables.
Kendall’s tau correlation measures the ordinal association between two measured quantities.

We also considered the use of the Mutual Information, but it was discarded due to its excessive time requirements.

### Reproducibility

Since the similarity matrices are, of course, quadratic in memory requirements, we cannot compute the full similarity matrix for all of the spectra. Instead, we sample `10_000` row and `10_000` column distinct spectra at each iteration, yielding a total of `100_000_000` similarity computations. We employ a `float32` data type for the similarity matrices, which allows us to store the full similarity matrix in memory.

We compute the Jaccard similarity between the fingerprints and the cosine similarity between the spectra, and then compute the aforementioned correlations. Each correlation provides both the correlation coefficient and the p-value, which we report in the results.

To reproduce these results, from the current directory, exeute the following command:

```bash
python cosine_similarity_evaluation.py --verbose\
                                       --iterations 10\
                                       --spectra 10000\
                                       --output cosine_correlations.csv
```

### Results

These are the preliminary results, more coming soon.

| smiles_fingerprint   | spectra_similarity   | spearman_correlation  | p_value |
|----------------------|----------------------|-----------------------|---------|
| ECFPFingerprint      | CosineGreedy         | 0.09587438021397068    | 0.0     |
| ECFPFingerprint      | NeutralLossesCosine  | 0.17668211865482553    | 0.0     |
| ECFPFingerprint      | ModifiedCosine       | 0.1646665227765613     | 0.0     |
| AvalonFingerprint    | CosineGreedy         | 0.054426792833399164   | 0.0     |
| AvalonFingerprint    | NeutralLossesCosine  | 0.06774335574922398    | 0.0     |
| AvalonFingerprint    | ModifiedCosine       | 0.051446778515837406   | 0.0     |
| RDKitFingerprint     | CosineGreedy         | 0.046329056643053326   | 0.0     |
| RDKitFingerprint     | NeutralLossesCosine  | 0.07381088792637187    | 0.0     |
| RDKitFingerprint     | ModifiedCosine       | 0.053875117708015174   | 0.0     |