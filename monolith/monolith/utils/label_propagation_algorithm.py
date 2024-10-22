"""Label Propagation Algorithm (LPA) implementation."""

from typing import List
import networkx as nx
import numpy as np
from typeguard import typechecked
from tqdm.auto import tqdm


@typechecked
def label_propagation_algorithm(
    graph: nx.Graph,
    features: np.ndarray,
    node_names: List[str],
    weight: str = "weight",
    threshold: float = 1e-5,
    normalize: bool = True,
    ignore_zeroed_nodes: bool = True,
    verbose: bool = True,
) -> np.ndarray:
    """Return LPA-ed classes.

    Parameters
    ----------
    graph : nx.Graph
        The graph whose topology will be used for the LPA.
    features : np.ndarray
        One-hot encoded features to propagate.
    node_names : List[str]
        The names of the nodes in the graph.
    weight : str
        Name of the edge attribute containing the weight of the edges.
    threshold : float
        The threshold to stop the LPA.
    normalize : bool
        Whether to normalize the features at each iteration.
    ignore_zeroed_nodes : bool
        Whether to ignore nodes with zero features.
    verbose : bool
        Whether to show a progress bar.
    """
    last_variation = np.inf

    # We prepare a reverse index for the node names, as we have no guarantee for the network
    # to have the nodes in the same order as the classes, or to have all the nodes.
    largest_node = max(int(node_name) for node_name in node_names)
    reverse_index = np.full(
        (largest_node + 1,), fill_value=10 * largest_node, dtype=int
    )
    for index, node_name in enumerate(node_names):
        reverse_index[int(node_name)] = index

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

    number_of_iterations = 0

    while last_variation > threshold:
        number_of_iterations += 1
        zeroed_mask: np.ndarray = features.sum(axis=1) == 0

        # We propagate the features
        new_features: np.ndarray = features.copy()
        for node in graph.nodes:
            weights: np.ndarray = np.fromiter(
                (
                    graph[node][neighbor][weight]
                    for neighbor in graph.neighbors(node)
                    if not ignore_zeroed_nodes
                    or not zeroed_mask[reverse_index[int(neighbor)]]
                ),
                dtype=float,
            )
            if weights.size == 0:
                continue
            assert weights.sum() != 0, "The sum of the weights must not be zero."

            weights_sum = weights.sum()

            # We include the node itself in the sum of the weights only if
            # it is not zeroed or if we are not ignoring zeroed nodes
            if not ignore_zeroed_nodes or not zeroed_mask[reverse_index[int(node)]]:
                weights_sum: float = weights_sum + 1
                new_features[reverse_index[int(node)]] = (
                    features[reverse_index[int(node)]] / weights_sum
                )

            normalized_weights: np.ndarray = weights / weights_sum

            for normalized_weight, neighbour_features in zip(
                normalized_weights,
                (
                    features[reverse_index[int(neighbor)]]
                    for neighbor in graph.neighbors(node)
                    if not ignore_zeroed_nodes
                    or not zeroed_mask[reverse_index[int(neighbor)]]
                ),
            ):

                new_features[reverse_index[int(node)]] += (
                    neighbour_features * normalized_weight
                )

        # We normalize the features
        if normalize:
            new_features = new_features / new_features.sum(axis=1)[:, None].clip(1e-10)

        # We compute the variation
        last_variation = np.linalg.norm(new_features - features)

        convergence_percentage = threshold / last_variation * 100

        features = new_features

        # We update the features
        global_progress_bar.update(n=convergence_percentage - global_progress_bar.n)
        global_progress_bar.set_postfix(
            {
                "Variation": last_variation,
            }
        )

    return features
