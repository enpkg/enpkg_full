"""Label Propagation Algorithm (LPA) implementation."""

import networkx as nx
import numpy as np
from tqdm.auto import tqdm
from numba import njit, prange


@njit(parallel=True)
def numba_label_propagation(
    features: np.ndarray,
    zeroed_mask: np.ndarray,
    weights_data: np.ndarray,
    weights_indices: np.ndarray,
    weights_indptr: np.ndarray,
) -> np.ndarray:
    """Executes one iteration of the LPA using Numba."""
    new_features = np.zeros_like(features)

    for node in prange(features.shape[0]):  # pylint: disable=not-an-iterable
        row_weights = weights_data[weights_indptr[node] : weights_indptr[node + 1]]
        neighbors = weights_indices[weights_indptr[node] : weights_indptr[node + 1]]

        # We include the node itself in the sum of the weights only if
        # it is not zeroed
        weights_sum = 0

        for neighbor, weight in zip(
            neighbors,
            row_weights,
        ):
            if not zeroed_mask[neighbor]:
                weights_sum += weight

        if not zeroed_mask[node]:
            weights_sum += 1
            for i in range(features.shape[1]):
                new_features[node, i] = features[node, i] / weights_sum

        if weights_sum == 0:
            continue

        for neighbor, normalized_weight in zip(neighbors, row_weights / weights_sum):
            for i in range(features.shape[1]):
                new_features[node, i] += features[neighbor, i] * normalized_weight

        zeroed_mask[node] = False

    return new_features


def label_propagation_algorithm(
    graph: nx.Graph,
    features: np.ndarray,
    node_names: list[str],
    weight: str = "weight",
    threshold: float = 1e-5,
    normalize: bool = True,
    verbose: bool = True,
) -> np.ndarray:
    """Return LPA-ed classes.

    Parameters
    ----------
    graph : nx.Graph
        The graph whose topology will be used for the LPA.
    features : np.ndarray
        One-hot encoded features to propagate.
    node_names : list[str]
        The names of the nodes in the graph.
    weight : str
        Name of the edge attribute containing the weight of the edges.
    threshold : float
        The threshold to stop the LPA.
    normalize : bool
        Whether to normalize the features at each iteration.
    verbose : bool
        Whether to show a progress bar.
    """
    assert features.shape[0] == len(node_names), (
        f"The number of features ({features.shape[0]}) must be the same as the number of nodes "
        f"({len(node_names)}) in the graph."
    )
    assert features.shape[1] > 0, "The number of features must be greater than 0."
    nan_count = np.sum(np.isnan(features))
    assert (
        nan_count == 0
    ), f"The features must not contain NaN, but it contains {nan_count}."
    inf_count = np.sum(np.isinf(features))
    assert (
        inf_count == 0
    ), f"The features must not contain infinite values, but it contains {inf_count}."

    last_variation = np.inf

    # We convert the graph into a SciPy sparse matrix
    weights = nx.to_scipy_sparse_array(graph, nodelist=node_names, weight=weight)

    global_progress_bar = tqdm(
        desc="LPA",
        total=100,
        dynamic_ncols=True,
        leave=False,
        disable=not verbose,
        bar_format="{l_bar}{bar}| {n:.2f}%",
    )

    # We normalize the features
    if normalize:
        features = features / features.sum(axis=1)[:, None].clip(1e-10)
    else:
        # If the user has requested to NOT normalize the features, we expect
        # for each value to be between 0 and 1.
        if features.min() < 0 or features.max() > 1:
            raise ValueError(
                "The features must be between 0 and 1 if the user has requested to NOT normalize them."
            )

    zeroed_mask: np.ndarray = features.sum(axis=1) == 0

    while True:
        new_features = numba_label_propagation(
            features, zeroed_mask, weights.data, weights.indices, weights.indptr
        )

        # We normalize the features
        if normalize:
            new_features = new_features / new_features.sum(axis=1)[:, None].clip(1e-10)

        # We compute the variation
        last_variation = np.linalg.norm(new_features - features)

        if last_variation < threshold:
            break

        convergence_percentage = (threshold / last_variation) * 100

        features = new_features

        # We update the features
        global_progress_bar.update(n=convergence_percentage - global_progress_bar.n)
        global_progress_bar.set_postfix(
            {
                "Variation": last_variation,
            }
        )

    return features
