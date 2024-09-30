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
        bool: lambda key, value: f"{key} = {str(value).lower()}",
    }

    # Define the operators mapping with a $ prefix for both symbols and string representations
    operators = {
        "$>": lambda key, value: f"{key} > {value}",
        "$gt": lambda key, value: f"{key} > {value}",
        "$>=": lambda key, value: f"{key} >= {value}",
        "$gte": lambda key, value: f"{key} >= {value}",
        "$<": lambda key, value: f"{key} < {value}",
        "$lt": lambda key, value: f"{key} < {value}",
        "$<=": lambda key, value: f"{key} <= {value}",
        "$lte": lambda key, value: f"{key} <= {value}",
        "$!=": lambda key, value: f"{key} != {value}",
    }

    def format_filter(key: str, value: Any) -> str:
        """Format a filter based on its type and handle nested properties and operators."""
        if isinstance(value, dict):
            # Handle operators
            for op, op_value in value.items():
                if op in operators:
                    return operators[op](key, op_value)  # type: ignore[no-untyped-call]
            # If no recognized operator is found, recurse into nested dictionaries
            return " and ".join(
                format_filter(f"{key}.{nested_key}", nested_value)
                for nested_key, nested_value in value.items()
            )
        else:
            formatter = formatters.get(type(value))
            if formatter:
                return formatter(key, value)
            else:
                raise ValueError(
                    f"Unsupported filter value type: {type(value)} for key: {key}"
                )

    jsonata_parts = [format_filter(key, value) for key, value in filters.items()]

    return " and ".join(jsonata_parts)
