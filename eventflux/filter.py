from collections.abc import Callable
from typing import Any


def translate_filters_to_jsonata(filters: dict[str, Any]) -> str:
    """
    Translates a dictionary of filters into a JSONata expression.

    The function iterates through the provided dictionary and constructs a JSONata expression
    based on the key-value pairs. The formatting logic for each data type is extensible
    via a mapping.

    Args:
        filters (dict[str, Any]): A dictionary where keys represent field names
                                   and values are the criteria to match.

    Returns:
        str: A JSONata expression as a string, combining all filters with 'and'.
    """
    # Define a mapping of types to their corresponding formatting functions
    formatters: dict[type, Callable[[str, Any], str]] = {
        str: lambda key, value: f'{key} = "{value}"',
        int: lambda key, value: f"{key} = {value}",
        float: lambda key, value: f"{key} = {value}",
        # Add more types and their corresponding formatting functions as needed
    }

    jsonata_parts = []

    for key, value in filters.items():
        formatter = formatters.get(type(value))
        if formatter:
            jsonata_parts.append(formatter(key, value))

    return " and ".join(jsonata_parts)
