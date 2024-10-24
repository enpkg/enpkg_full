"""Test that LPA works as intended."""

import pandas as pd
import numpy as np
import networkx as nx
from monolith.utils import label_propagation_algorithm


def test_lpa():
    """Test that LPA works as intended."""

    # We read the weighted edge list from a TSV
    graph: nx.Graph = nx.read_weighted_edgelist("tests/graph.edgelist")

    # We read the features from a NPY
    features: np.ndarray = np.load("tests/features.npy")

    # We read the node names from a TXT
    node_names: list[str] = (
        pd.read_csv("tests/node_names.txt", header=None, dtype=str).values.flatten().tolist()
    )

    # We ensure that the graph has all of the nodes, including those
    # that are singletons.
    graph.add_nodes_from(node_names)

    # We run the LPA
    propagated_features: np.ndarray = label_propagation_algorithm(
        graph,
        features,
        node_names,
        threshold=1e-5,
        normalize=False,
        verbose=True,
    )

    assert (
        propagated_features is not None
    ), "The LPA did not return any propagated features."
    assert (
        propagated_features.shape == features.shape
    ), "The shape of the propagated features is not the same as the original features."
    assert (
        not np.isnan(propagated_features).any()
    ), "The propagated features contain NaN values."
    assert (
        not np.isinf(propagated_features).any()
    ), "The propagated features contain infinite values."
    assert (
        not np.allclose(features, propagated_features)
    ), "The features were not propagated."