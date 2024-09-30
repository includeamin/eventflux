import pytest

from eventflux.filter import translate_filters_to_jsonata


def test_translate_single_string_filter():
    """Test translating a single string filter."""
    filters = {"name": "Alice"}
    expected = 'name = "Alice"'
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_single_integer_filter():
    """Test translating a single integer filter."""
    filters = {"age": 30}
    expected = "age = 30"
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_single_float_filter():
    """Test translating a single float filter."""
    filters = {"balance": 1000.75}
    expected = "balance = 1000.75"
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_multiple_filters():
    """Test translating multiple simple filters."""
    filters = {"name": "Alice", "age": 30, "balance": 1000.75}
    expected = 'name = "Alice" and age = 30 and balance = 1000.75'
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_nested_filters():
    """Test translating nested filters."""
    filters = {
        "user": {"name": "Alice", "age": 30},
        "account": {"balance": 1000.75, "status": "active"},
    }
    expected = (
        'user.name = "Alice" and user.age = 30 and '
        'account.balance = 1000.75 and account.status = "active"'
    )
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_unsupported_type():
    """Test that ValueError is raised for unsupported filter value types."""
    filters = {"is_active": {True}}  # Unsupported type (set)

    with pytest.raises(
        ValueError,
        match="Unsupported filter value type: <class 'set'> for key: is_active",
    ):
        translate_filters_to_jsonata(filters)


def test_translate_empty_filters():
    """Test translating an empty filter dictionary."""
    filters = {}
    expected = ""
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_nested_properties_with_different_types():
    """Test translating nested properties with mixed value types."""
    filters = {
        "user": {
            "name": "Alice",
            "age": 30,
            "height": 5.5,
        },
        "account": {"balance": 1000.0, "status": "active"},
    }
    expected = (
        'user.name = "Alice" and user.age = 30 and user.height = 5.5 and '
        'account.balance = 1000.0 and account.status = "active"'
    )
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_operator_filters():
    """Test translating filters with comparison operators using $ prefixed symbols."""
    filters = {
        "user": {"age": {"$gt": 25}, "name": "Alice"},
        "account": {"balance": {"$lte": 1000.0}, "status": "active"},
    }
    expected = (
        'user.age > 25 and user.name = "Alice" and '
        'account.balance <= 1000.0 and account.status = "active"'
    )
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_combined_filters_with_operators():
    """Test translating filters with multiple operators and simple conditions."""
    filters = {
        "product": {"price": {"$lt": 50}, "available": True},
        "order": {"quantity": {"$gte": 10}, "status": "completed"},
    }
    expected = (
        "product.price < 50 and product.available = true and "
        'order.quantity >= 10 and order.status = "completed"'
    )
    assert translate_filters_to_jsonata(filters) == expected


def test_translate_combined_filters_with_unsupported_type():
    """Test that ValueError is raised for unsupported filter types with operators."""
    filters = {
        "user": {"age": {"$gt": 25}, "is_active": {True}}  # Unsupported type (set)
    }

    with pytest.raises(
        ValueError,
        match="Unsupported filter value type: <class 'set'> for key: user.is_active",
    ):
        translate_filters_to_jsonata(filters)
