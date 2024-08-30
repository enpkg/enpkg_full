"""Submodule providing a binary search by key function."""

from typing import Any, Callable, List, Optional, Tuple


def binary_search_by_key(
    key: Any,
    array: List[Any],
    key_func: Callable[[Any], Any],
    left: Optional[int] = None,
    right: Optional[int] = None,
) -> Tuple[bool, int]:
    """Search for a key in a sorted array using a key function.

    Args:
        key: The key to search for.
        array: The sorted array to search in.
        key_func: A function that extracts the key from an array element.
        left: The left index of the search range.
        right: The right index of the search range.

    Returns:
        A tuple with a boolean indicating if the key was found and the index of the key.
    """
    assert key is not None, "Key should not be None"
    if left is None:
        left = 0
    if right is None:
        right = len(array) - 1

    while left <= right:
        mid = left + (right - left) // 2
        mid_key = key_func(array[mid])

        assert (
            mid_key is not None
        ), f"Key function for value {array[mid]} should not return None"

        if mid_key == key:
            return True, mid
        if mid_key < key:
            left = mid + 1
        else:
            right = mid - 1

    return False, left
