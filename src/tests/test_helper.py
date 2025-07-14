"""Test helpers."""

from dataplaybook import helper


def test_format_as_table() -> None:
    """Test."""
    header = ["Name", "Age", "Sex"]
    keys = ["name", "age", "sex"]
    sort_by_key = "age"
    sort_order_reverse = True
    data = [
        {"name": "John Doe", "age": 37, "sex": "M"},
        {"name": "Lisa Simpson", "age": 17, "sex": "F"},
        {"name": "Bill Clinton", "age": 57, "sex": "M"},
    ]

    res = helper.format_as_table(data, keys, header, sort_by_key, sort_order_reverse)

    assert res
