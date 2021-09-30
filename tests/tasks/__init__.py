"""Init."""

from dataplaybook.tasks.gis import linestring


def test_linestring():
    """Test linestring."""
    res = linestring([{"latA": 1, "latB": 2, "lonA": 3, "lonB": 4}])
    assert res
