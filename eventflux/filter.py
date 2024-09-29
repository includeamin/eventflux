import jsonata
from typing import Dict, Any


def translate_filters_to_jsonata(filters: Dict[str, Any]) -> str:
    """
    Translates a dictionary of filters into a JSONata expression.

    Args:
        filters (dict): A dictionary where the keys are the field names and the values are the values to match.

    Returns:
        str: The corresponding JSONata expression as a string.
    """
    jsonata_parts = []

    for key, value in filters.items():
        if isinstance(value, str):
            # Translate simple key-value pairs
            jsonata_parts.append(f'{key} = "{value}"')
        elif isinstance(value, int | float):
            # For numerical values, just add them directly without quotes
            jsonata_parts.append(f"{key} = {value}")
        elif isinstance(value, list):
            # Handle lists (e.g., field should match any value in a list)
            jsonata_parts.append(f'{key} in [{", ".join(map(str, value))}]')
        # Extend here to handle more complex cases like ranges, regex, etc.
        # elif isinstance(value, SomeOtherType):
        #     jsonata_parts.append(f'...')

    # Join all parts with 'and' for a combined expression
    return " and ".join(jsonata_parts)


# Example usage of the translator
filters = {"name": "example.user.created", "age": 30, "roles": ["admin", "user"]}

jsonata_expr_str = translate_filters_to_jsonata(filters)
compiled_jsonata_expr = jsonata.Jsonata(jsonata_expr_str)
print(f"Translated JSONata Expression: {jsonata_expr_str}")
