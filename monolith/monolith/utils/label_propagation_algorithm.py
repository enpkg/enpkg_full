"""Label Propagation Algorithm (LPA) implementation."""
from typing import List
import networkx as nx
import numpy as np
from tqdm.auto import tqdm


def label_propagation_algorithm(
    graph: nx.Graph,
    classes: np.ndarray,
    node_names: List[str],
    imputation: str = "uniform",
    weight: str = "weight",
    threshold: float = 1e-5,
    verbose: bool = True,
) -> np.ndarray:
    """Return LPA-ed classes.

    Parameters
    ----------
    graph : nx.Graph
        The graph whose topology will be used for the LPA.
    classes : np.ndarray
        One-hot encoded classes to propagate.
    node_names : List[str]
        The names of the nodes in the graph.
    imputation : str
        The imputation strategy to use for the entries with no labels. Options are:
            * "uniform": initialize the features using a uniform distribution.
            * "zero": leaves the features as zeros.
    weight : str
        Name of the edge attribute containing the weight of the edges.
    threshold : float
        The threshold to stop the LPA.
    verbose : bool
        Whether to show a progress bar.
    """
    # Initialize the features
    if imputation == "uniform":
        # We initialize the vector of features that have no labels
        # i.e. they sum to zero to the uniform distribution
        zeroed_classes = np.where(classes.sum(axis=1) == 0)[0]

        # We set the features to the uniform distribution
        features = classes.copy()
        features[zeroed_classes] = 1 / features.shape[1]
    elif imputation == "zero":
        # Nothing to do as the features are already zeros
        features = classes.copy()
    else:
        raise ValueError(f"Imputation strategy {imputation} not recognized.")

    last_variation = np.inf
    iteration_number = 0

    # We prepare the reverse index for the node names.
    assert set(node_names) == set(graph.nodes), "The node names must be the same as the graph nodes."

    # We prepare a reverse index for the node names
    largest_node = max(int(node_name) for node_name in node_names)
    reverse_index = np.full((largest_node + 1, ), fill_value=10*largest_node, dtype=int)
    for index, node_name in enumerate(node_names):
        reverse_index[int(node_name)] = index

    global_progress_bar = tqdm(
        desc="Layer Propagation Algorithm",
        dynamic_ncols=True,
        leave=False,
        disable=not verbose,
    )

    while last_variation > threshold:
        # We normalize the features
        features = features / features.sum(axis=1)[:, None]

        # We propagate the features
        new_features = np.zeros_like(features)
        for node in tqdm(
            graph.nodes,
            desc=f"Iteration {iteration_number}",
            dynamic_ncols=True,
            leave=False,
            disable=not verbose,
        ):
            for neighbor in graph.neighbors(node):
                new_features[reverse_index[int(node)]] += features[reverse_index[int(neighbor)]] * graph[node][neighbor][weight]

        # We normalize the features
        new_features = new_features / new_features.sum(axis=1)[:, None]

        # We compute the variation
        last_variation = np.linalg.norm(new_features - features)

        # We update the features
        iteration_number += 1
        global_progress_bar.update()
        global_progress_bar.set_postfix({"Variation": last_variation})

    return features