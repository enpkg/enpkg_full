"""Label Propagation Algorithm (LPA) implementation."""

from typing import List
import networkx as nx
import numpy as np
from tqdm.auto import tqdm


def label_propagation_algorithm(
    graph: nx.Graph,
    features: np.ndarray,
    node_names: List[str],
    weight: str = "weight",
    threshold: float = 1e-5,
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
    verbose : bool
        Whether to show a progress bar.
    """

    last_variation = np.inf
    iteration_number = 0

    # We prepare a reverse index for the node names, as we have no guarantee for the network
    # to have the nodes in the same order as the classes, or to have all the nodes.
    largest_node = max(int(node_name) for node_name in node_names)
    reverse_index = np.full(
        (largest_node + 1,), fill_value=10 * largest_node, dtype=int
    )
    for index, node_name in enumerate(node_names):
        reverse_index[int(node_name)] = index

    global_progress_bar = tqdm(
        desc="Layer Propagation Algorithm",
        dynamic_ncols=True,
        leave=False,
        disable=not verbose,
    )

    # We normalize the features
    features = features / features.sum(axis=1)[:, None].clip(1e-10)

    while last_variation > threshold:

        # We propagate the features
        new_features = features.copy()
        for node in graph.nodes:
            for neighbor in graph.neighbors(node):
                new_features[reverse_index[int(node)]] += (
                    features[reverse_index[int(neighbor)]]
                    * graph[node][neighbor][weight]
                )

        # We normalize the features
        new_features = new_features / new_features.sum(axis=1)[:, None].clip(1e-10)

        # We compute the variation
        last_variation = np.linalg.norm(new_features - features)

        convergence_percentage = threshold / last_variation * 100

        features = new_features

        # We update the features
        iteration_number += 1
        global_progress_bar.update()
        global_progress_bar.set_postfix(
            {
                "Convergence": f"{convergence_percentage:.2f}%",
                "Variation": last_variation,
            }
        )

    return features
